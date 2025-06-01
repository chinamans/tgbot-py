# 标准库
import os
import uuid
from pathlib import Path

# 第三方库
import imgkit


async def generate_command_table_image(data, title="📘 命令一览表"):
    # wkhtmltoimage 路径（根据系统设置）
    if os.name == "nt":
        wkhtmltoimage_path = r"D:\Tool Software\wkhtmltopdf\bin\wkhtmltoimage.exe"
        wkhtml_config = imgkit.config(wkhtmltoimage=wkhtmltoimage_path)
    else:
        wkhtml_config = None

    # 构造表格行
    rows = ""
    for cmd, usage, example, note in data:
        rows += f"""
        <tr>
            <td>{cmd}</td>
            <td>{usage}</td>
            <td>{example}</td>
            <td>{note}</td>
        </tr>
        """

    # 生成 HTML 字符串
    html_str = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Microsoft YaHei', sans-serif;
            }}
            table {{
                border-collapse: collapse;                
                font-size: 14px;
            }}
            th, td {{
                border: 1px solid #666;
                padding: 6px 10px;
                text-align: center;
            }}
            thead {{
                background-color: #4a72b2;
                color: white;
            }}
            caption {{
                caption-side: top;
                font-size: 16px;
                font-weight: bold;
                background-color: #4a72b2;
                color: white;
                padding: 6px;
                border: 1px solid #999;
            }}
            td:first-child, th:first-child,
            td:nth-child(3), th:nth-child(3) {{
                white-space: nowrap;
            }}
        </style>
    </head>
    <body>
        <table>
            <caption>{title}</caption>
            <thead>
                <tr>
                    <th>命令</th>
                    <th>作用</th>
                    <th>举例</th>
                    <th>说明</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </body>
    </html>
    """

    # 写入临时 HTML 文件
    #  
    unique_id = uuid.uuid4().hex
    html_file = Path(f"temp_file/command_temp_{unique_id}.html")
    img_file = Path(f"temp_file/command_table_{unique_id}.png")
    html_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_str)

        
    options = {
        'encoding': "UTF-8",
        'format': 'png',
        'width': 800,
        'enable-local-file-access': '',
        'quiet': ''
    }

    imgkit.from_file(str(html_file), str(img_file), options=options, config=wkhtml_config)

    Path(html_file).unlink()    
    return img_file
