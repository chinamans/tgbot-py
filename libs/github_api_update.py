import json
import logging
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Union, Optional, List, Dict, Any
from urllib.error import HTTPError, URLError


# --- 配置区域 ---
GITHUB_TOKEN: str = ""  # 全局 GitHub_token, 用于提高 API 请求速率限制
GITHUB_PROXY: str = (
    ""  # GitHub 代理, 例如 "https://gh-proxy.com/" # 注意: 代理仅对 'github.com' 的 URL 有效，'api.github.com' 的请求不通过代理。
)
CHECK_INTERVAL: int = 5 * 60  # 检查间隔时间 (单位: 秒)

DEBUG_MODE: bool = False  # 是否启用调试模式
LOGGING_LEVEL: str = "DEBUG"  # 日志级别, 可选: DEBUG, INFO, WARNING, ERROR, CRITICAL

# 仓库监控配置
# 监控的仓库列表，每个仓库配置包含:
# - type: 监控类型 ('release' 或 'branch_source')
# - repo: 仓库全名 (例如 'owner/repo_name')
# - release_type: 仅对 'release' 类型有效，指定获取的 Release 类型 ('Latest', 'Pre-release' 或 None)；留空时，视为None，获取所有 Release 取第一个值。
# - token: 可选的仓库特定 token (如果需要访问私有仓库或提高速率限制)
# - asset_patterns: 仅对 'release' 类型有效，指定要下载的 Release 附件匹配模式 (例如 ['dist.zip'])
# - download_dir: 下载目录路径 (必须是绝对路径，最终保存的路径)


# --- 状态文件和日志文件路径 ---
__STATE_FILE = "github_monitor_state.json"
__LOG_FILE = "github_monitor.log"

# --- 日志配置 ---
logging.basicConfig(
    level=(
        logging.DEBUG
        if DEBUG_MODE
        else getattr(logging, LOGGING_LEVEL.upper(), logging.INFO)
    ),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(__LOG_FILE, encoding="utf-8"),
    ],
)


def _get_effective_url_for_github_com(base_url: str) -> str:
    """
    仅对 'github.com' (非 'api.github.com') 的 URL 应用 GITHUB_PROXY。
    代理拼接方式: GITHUB_PROXY + base_url
    """
    if GITHUB_PROXY and "github.com" in base_url and "api.github.com" not in base_url:
        # 确保代理以 / 结尾，如果它本身不以 / 结尾且 base_url 不以 https:// 开头
        proxy_prefix = GITHUB_PROXY.rstrip("/")
        # 直接拼接
        effective_url = f"{proxy_prefix}/{base_url}"
        logging.debug(
            f"应用代理: {proxy_prefix}, 原始URL: {base_url}, 拼接后URL: {effective_url}"
        )
        return effective_url
    return base_url


def make_github_api_request(
    url: str, repo_token: Optional[str] = None
) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """
    向 GitHub API (api.github.com) 发送请求。API 请求不通过 GITHUB_PROXY。

    :param url: API Endpoint URL (必须是 api.github.com 的链接)。
    :param repo_token: 仓库特定的 Token，优先于全局 GITHUB_TOKEN。
    :return: 解析后的 JSON 数据 (dict 或 list)，如果请求失败则返回 None。
    """
    if "api.github.com" not in url:
        raise ValueError(
            f"make_github_api_request 仅用于 api.github.com 的链接，收到: {url}"
        )

    headers = {"Accept": "application/vnd.github.v3+json"}
    # 优先使用仓库特定 token，其次是全局 GITHUB_TOKEN
    auth_token = repo_token if repo_token else GITHUB_TOKEN
    if auth_token:
        headers["Authorization"] = f"token {auth_token}"

    logging.debug(
        f"发起 API 请求: {url}，头部键: {list(headers.keys())}"
    )  # 避免打印整个头部（可能含token）
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            response_content = response.read().decode()
            if response.status == 200:
                parsed_json = json.loads(response_content)
                if isinstance(parsed_json, (dict, list)):
                    return parsed_json  # type: ignore
                else:
                    logging.error(
                        f"GitHub API 请求 {url} 返回的 JSON 不是 dict 或 list: {type(parsed_json)}"
                    )
                    return None
            else:
                logging.error(
                    f"GitHub API 请求失败: {url} - 状态码: {response.status}, 信息: {response_content}"
                )
                return None
    except HTTPError as err:
        error_response_content = ""
        try:
            error_response_content = err.read().decode()
        except Exception:
            pass
        logging.error(
            f"GitHub API HTTPError: {url} - 状态码: {err.code}, 原因: {err.reason}, 响应体 (部分): {error_response_content[:200]}"
        )
        if err.code == 404:
            logging.warning(f"资源未找到 (404): {url}")
        elif err.code == 403 and "API rate limit exceeded" in error_response_content:
            logging.error(f"API 速率限制已超出 ({url})。请检查 Token 或等待重置。")
        elif err.code == 401:
            logging.error(
                f"API 请求认证失败 (401 Unauthorized) for {url}。请检查 Token 权限。"
            )
        return None
    except URLError as err:
        logging.error(f"GitHub API URLError: {url} - 原因: {err.reason}")
        return None
    except json.JSONDecodeError as err:
        logging.error(f"GitHub API 响应 JSON 解析错误: {url} - {err}")
        return None
    except Exception as err:
        logging.error(f"GitHub API 请求时发生未知错误: {url} - {err}", exc_info=True)
        return None


def download_file(
    url: str,
    destination_path: Path,
    repo_token: Optional[str] = None,
    is_source_archive: bool = False,
):
    """
    下载文件到指定路径。

    :param url: 文件下载 URL。
    :param destination_path: 本地保存路径 (Path 对象)。
    :param repo_token: 仓库特定的 Token (主要用于 API 下载的 release assets)。
    :param is_source_archive: 标记是否为直接的源码归档链接 (如 github.com/.../archive.zip)。
    """
    if is_source_archive:
        effective_url = _get_effective_url_for_github_com(url)
    else:
        effective_url = url

    headers = {}
    auth_token_to_use = repo_token if repo_token else GITHUB_TOKEN

    # 对于 API 下载的 release assets (通常包含 api.github.com 或 assets.github.com)
    if (
        not is_source_archive
        and auth_token_to_use
        and (
            "api.github.com/repos" in effective_url
            and "/assets/" in effective_url
            or "assets.github.com" in effective_url
        )
    ):
        headers["Accept"] = "application/octet-stream"
        headers["Authorization"] = f"token {auth_token_to_use}"

    logging.debug(
        f"准备下载文件: {effective_url} 到 {destination_path}，头部键: {list(headers.keys())}"
    )
    req = urllib.request.Request(effective_url, headers=headers)
    try:
        with (
            urllib.request.urlopen(req, timeout=300) as response,
            open(destination_path, "wb") as out_file,
        ):
            if response.status == 200:
                shutil.copyfileobj(response, out_file)
                logging.info(f"文件已下载: {destination_path} ")
            else:
                logging.error(
                    f"下载文件失败: {effective_url} - 状态码: {response.status}"
                )
                if destination_path.exists():
                    destination_path.unlink(missing_ok=True)
                raise Exception(f"下载文件失败，状态码: {response.status}")
    except HTTPError as err:
        logging.error(
            f"下载文件时发生 HTTPError: {effective_url} - 状态码: {err.code}, 原因: {err.reason}"
        )
        if destination_path.exists():
            destination_path.unlink(missing_ok=True)
        raise
    except Exception as err:
        logging.error(f"下载文件时发生错误: {effective_url} - {err}", exc_info=True)
        if destination_path.exists():
            destination_path.unlink(missing_ok=True)
        raise


def load_state() -> Dict[str, Any]:
    """
    从状态文件加载当前记录状态，如果文件不存在或格式错误，则返回空字典。
    """
    state_path = Path(__STATE_FILE)
    if state_path.exists():
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    logging.info(f"状态文件 {__STATE_FILE} 为空，初始化记录状态。")
                    return {}
                return json.loads(content)
        except json.JSONDecodeError:
            logging.warning(f"状态文件 {__STATE_FILE} 格式错误，初始化记录状态。")
            return {}
        except Exception as err:
            logging.error(
                f"加载状态文件 {__STATE_FILE} 时发生错误: {err}。初始化记录状态。"
            )
            return {}
    return {}


def save_state(state: Dict[str, Any]):
    """
    保存当前记录状态到指定的状态文件。
    """
    state_path = Path(__STATE_FILE)
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
    except IOError as err:
        logging.error(f"无法保存记录状态到 {__STATE_FILE}: {err}")


def manage_path(
    path_str: str, clear_before_op: bool = False, ensure_exists: bool = True
) -> Path:
    """
    管理指定路径的创建和清理。
    :param path_str: 目标路径字符串。
    :param clear_before_op: 是否在操作前清空目录。
    :param ensure_exists: 是否确保目录存在，如果不存在则创建。
    """
    path = Path(path_str)
    if clear_before_op and path.exists():
        logging.info(f"清空目标目录: {path}")
        for item in path.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    if ensure_exists:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_temp_cache_dir_path(
    repo_type: str, repo_full_name: str, sub_identifier: Optional[str] = None
) -> Path:
    """
    根据仓库类型和名称生成临时缓存目录路径。
    :param repo_type: 仓库类型 ('release' 或 'branch_source')。
    :param repo_full_name: 仓库全名 (例如 'owner/repo_name')。
    :param sub_identifier: 可选的子标识符，用于进一步区分目录。
    :return: 临时缓存目录的 Path 对象。
    """
    repo_identifier = repo_full_name.replace("/", "_")
    sanitized_sub_identifier = (
        sub_identifier.lower().replace("-", "_").replace(" ", "_")
        if sub_identifier
        else None
    )
    dir_name_parts = [repo_type, repo_identifier]
    if sanitized_sub_identifier:
        dir_name_parts.append(sanitized_sub_identifier)
    temp_dir_leaf_name = "_".join(dir_name_parts)
    temp_base_dir = Path(tempfile.gettempdir())
    cache_dir_path = temp_base_dir / temp_dir_leaf_name
    return cache_dir_path


def get_default_branch(
    repo_full_name: str, repo_config_token: Optional[str] = None
) -> Optional[str]:
    """
    通过 GitHub API 获取仓库的默认分支名称。
    使用仓库特定 token (如果提供)，否则使用全局 token。
    """
    api_url = f"https://api.github.com/repos/{repo_full_name}"
    # API 请求不走代理，直接使用原始 URL
    repo_data = make_github_api_request(api_url, repo_token=repo_config_token)
    if repo_data and isinstance(repo_data, dict):
        default_branch = repo_data.get("default_branch")
        if default_branch:
            logging.info(f"仓库 {repo_full_name} 的默认分支是: {default_branch}")
            return default_branch
        else:
            logging.warning(f"无法从 API 获取仓库 {repo_full_name} 的默认分支信息。")
    else:
        logging.warning(f"获取仓库 {repo_full_name} 信息失败，无法确定默认分支。")
    return None


def unzip(temp_zip_path, source_archive_url, temp_dir_path, download_dir_str):
    if not temp_zip_path.exists() or temp_zip_path.stat().st_size == 0:
        raise Exception(f"源码下载失败或为空文件: {source_archive_url}")

    extract_path = temp_dir_path / "extracted_source"
    extract_path.mkdir()
    logging.debug(f"正在解压源码到: {extract_path}")
    with zipfile.ZipFile(temp_zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    extracted_items = list(extract_path.iterdir())
    if not extracted_items or not extracted_items[0].is_dir():
        raise Exception(
            f"解压后源码目录结构不符: {extract_path}, 内容: {[i.name for i in extracted_items]}"
        )

    source_content_dir = extracted_items[0]
    logging.debug(f"源码内容位于: {source_content_dir}")
    target_download_dir = manage_path(
        download_dir_str, clear_before_op=True, ensure_exists=True
    )

    logging.debug(f"正在移动文件到目标目录: {target_download_dir}")
    for item in source_content_dir.iterdir():
        shutil.move(str(item), str(target_download_dir / item.name))
    logging.info(f"源码已成功部署到: {target_download_dir}")


def process_release_repo(config: Dict[str, Any], current_states: Dict[str, Any]):
    repo_full_name = config.get("repo", "")
    download_dir_str = config.get("download_dir", "")
    repo_specific_token = config.get("token")  # 获取仓库特定 token

    repo_state = current_states.get("release", {}).get(repo_full_name, {})
    last_known_id = repo_state.get("id")

    api_base = "https://api.github.com/repos"  # API URL 不应被代理修改

    api_url = f"{api_base}/{repo_full_name}/releases/latest"
    latest_release = make_github_api_request(api_url, repo_token=repo_specific_token)

    latest_release_id = latest_release.get("id")
    latest_release_tag = latest_release.get("tag_name")
    latest_release_name = latest_release.get("name")

    if not latest_release_id:
        logging.error(f"无法从 {repo_full_name} Release 获取 ID。")
        return
    if str(latest_release_id) == str(last_known_id):
        logging.info(
            f"{repo_full_name} (Version: {latest_release_tag}, ID: {last_known_id}) Release 没有更新。"
        )
        return

    logging.info(
        f"{repo_full_name} 发现新 Release: '{latest_release_name}' (V: {latest_release_tag}, ID: {latest_release_id})"
    )
    temp_dir_path = get_temp_cache_dir_path("release", repo_full_name)

    if temp_dir_path.exists():
        shutil.rmtree(temp_dir_path)
    temp_dir_path.mkdir(parents=True, exist_ok=True)

    logging.debug(f"已创建临时缓存目录: {temp_dir_path}")
    target_download_dir = manage_path(
        download_dir_str, clear_before_op=False, ensure_exists=True
    )

    source_archive_url = latest_release.get("zipball_url")
    release_file = f"{latest_release_name}.zip"
    temp_zip_path = temp_dir_path / release_file
    logging.info(f"准备下载附件: {release_file} 从 {source_archive_url}")
    download_file(
        source_archive_url,
        temp_zip_path,
        repo_token=repo_specific_token,
        is_source_archive=False,
    )
    unzip(temp_zip_path, source_archive_url, temp_dir_path, target_download_dir)
    current_states.setdefault("release", {}).setdefault(repo_full_name, {})
    current_states["release"][repo_full_name]["id"] = str(latest_release_id)
    current_states["release"][repo_full_name]["version"] = latest_release_tag


def process_branch_repo(config: Dict[str, Any], current_states: Dict[str, Any]):
    repo_full_name = config.get("repo", "")
    branch_name_config = config.get("branch_name", "")
    download_dir_str = config.get("download_dir", "")
    repo_specific_token = config.get("token")

    if not repo_full_name:
        logging.error("仓库配置中缺少 'repo' 字段。")
        return
    if not download_dir_str:
        logging.error(f"仓库 {repo_full_name} 的 download_dir 未指定。")
        return

    effective_branch_name = branch_name_config
    if not effective_branch_name:
        logging.info(f"仓库 {repo_full_name} 未指定分支，尝试获取默认分支...")
        effective_branch_name = get_default_branch(
            repo_full_name, repo_config_token=repo_specific_token
        )
        if not effective_branch_name:
            logging.error(f"无法确定仓库 {repo_full_name} 的默认分支，跳过。")
            return

    logging.info(
        f"正在检查分支 Commit 更新: {repo_full_name} (分支: {effective_branch_name})"
    )
    repo_branch_state = (
        current_states.get("branch_source", {})
        .get(repo_full_name, {})
        .get(effective_branch_name, {})
    )
    last_known_sha = repo_branch_state.get("commits")

    api_url = f"https://api.github.com/repos/{repo_full_name}/commits?sha={effective_branch_name}&per_page=1"
    commit_data_list = make_github_api_request(api_url, repo_token=repo_specific_token)

    if (
        not commit_data_list
        or not isinstance(commit_data_list, list)
        or not commit_data_list[0]
    ):
        logging.warning(
            f"无法获取 {repo_full_name} 分支 {effective_branch_name} 的最新 Commit。"
        )
        return

    latest_commit = commit_data_list[0]
    latest_commit_sha = latest_commit.get("sha")

    if not latest_commit_sha:
        logging.error(
            f"无法从 Commit 获取 SHA: {repo_full_name}@{effective_branch_name}"
        )
        return
    if latest_commit_sha == last_known_sha:
        logging.info(
            f"{repo_full_name}@{effective_branch_name} 无新 Commit (SHA: {last_known_sha[:7] if last_known_sha else 'N/A'})."
        )
        return

    commit_msg = latest_commit.get("commit", {}).get("message", "").splitlines()[0]
    logging.info(
        f'{repo_full_name}@{effective_branch_name} 新 Commit: {latest_commit_sha[:7]} ("{commit_msg}")'
    )
    temp_dir_path = get_temp_cache_dir_path(
        "branch_source", repo_full_name, effective_branch_name
    )

    if temp_dir_path.exists():
        shutil.rmtree(temp_dir_path)
    temp_dir_path.mkdir(parents=True, exist_ok=True)
    logging.debug(f"已创建临时缓存目录: {temp_dir_path}")

    source_archive_url = (
        f"https://github.com/{repo_full_name}/archive/{effective_branch_name}.zip"
    )
    safe_branch_name = effective_branch_name.replace("/", "_")
    temp_zip_path = (
        temp_dir_path
        / f"{repo_full_name.replace('/', '_')}-{safe_branch_name}-latest.zip"
    )

    logging.info(f"准备下载源码: {source_archive_url}")
    # 源码归档下载，is_source_archive=True。Token 对此链接通常无效，但会通过代理。
    download_file(
        source_archive_url, temp_zip_path, repo_token=None, is_source_archive=True
    )

    if not temp_zip_path.exists() or temp_zip_path.stat().st_size == 0:
        raise Exception(f"源码下载失败或为空文件: {source_archive_url}")

    extract_path = temp_dir_path / "extracted_source"
    extract_path.mkdir()
    logging.debug(f"正在解压源码到: {extract_path}")
    with zipfile.ZipFile(temp_zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    extracted_items = list(extract_path.iterdir())
    if not extracted_items or not extracted_items[0].is_dir():
        raise Exception(
            f"解压后源码目录结构不符: {extract_path}, 内容: {[i.name for i in extracted_items]}"
        )

    source_content_dir = extracted_items[0]
    logging.debug(f"源码内容位于: {source_content_dir}")
    target_download_dir = manage_path(
        download_dir_str, clear_before_op=True, ensure_exists=True
    )

    logging.debug(f"正在移动文件到目标目录: {target_download_dir}")
    for item in source_content_dir.iterdir():
        shutil.move(str(item), str(target_download_dir / item.name))
    logging.info(f"源码已成功部署到: {target_download_dir}")

    current_states.setdefault("branch_source", {}).setdefault(
        repo_full_name, {}
    ).setdefault(effective_branch_name, {})
    current_states["branch_source"][repo_full_name][effective_branch_name][
        "commits"
    ] = latest_commit_sha
    logging.debug(
        f"成功处理 {repo_full_name}@{effective_branch_name} 新 Commit。已更新状态。"
    )


if __name__ == "__main__":
    if GITHUB_TOKEN:
        logging.info("全局 GITHUB_TOKEN 已设置。")
    else:
        logging.warning(
            "全局 GITHUB_TOKEN 未设置。API 请求频率将受限，且无法访问私有仓库。"
        )

    if GITHUB_PROXY:
        logging.info(f"将使用 GitHub 代理: {GITHUB_PROXY}")
    else:
        logging.info("未配置 GitHub 代理。")

    current_states = load_state()
    logging.info(
        f"已加载状态: {json.dumps(current_states, indent=2, ensure_ascii=False) if current_states else '无 (首次运行或状态文件丢失)'}"
    )
    logging.info("开始监控 GitHub 仓库...")
    process_release_repo(
        {
            "type": "release",
            "repo": "DonneChang/tgbot-py",
            "download_dir": "test",
        },
        current_states,
    )
    # process_branch_repo(
    #     {
    #         "type": "branch_source",
    #         "repo": "DonneChang/tgbot-py",
    #         "branch_name": "main",
    #         "download_dir": "test",
    #     },
    #     current_states,
    # )
    save_state(current_states)
