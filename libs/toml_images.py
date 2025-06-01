# 标准库
import os
import uuid
from pathlib import Path

# 第三方库
import imgkit
from pygments import highlight
from pygments.lexers.configs import IniLexer
from pygments.formatters import HtmlFormatter

async def toml_file_to_image(toml_file_path: Path):
    if os.name == "nt":
        wkhtmltoimage_path = r"D:\Tool Software\wkhtmltopdf\bin\wkhtmltoimage.exe"
        wkhtml_config = imgkit.config(wkhtmltoimage=wkhtmltoimage_path)
    else:
        wkhtml_config = None

  
    with open(toml_file_path, "r", encoding="utf-8") as f:
        toml_code = f.read()

    # 生成唯一文件名
    unique_id = uuid.uuid4().hex
    html_file = Path(f"temp_file/state_temp_{unique_id}.html")
    img_file = Path(f"temp_file/state_table_{unique_id}.png")
    html_file.parent.mkdir(parents=True, exist_ok=True)

    # 用 pygments 生成 HTML
    formatter = HtmlFormatter(full=True, linenos=True, style="colorful")
    html = highlight(toml_code, IniLexer(), formatter)

    # 写 HTML 文件
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html)


    options = {
        'encoding': "UTF-8",
        'format': 'png',
        'enable-local-file-access': '',
        'quiet': ''
    }

    imgkit.from_file(str(html_file), str(img_file), options=options, config=wkhtml_config)

    # 返回图片路径
    Path(html_file).unlink() 
    return img_file
