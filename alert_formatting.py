

# HTML Alert Generation Functions
def get_template():
    template_begin = """<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8"/>
        <meta content="Plan Text" property="og:title"/>
        <meta content="Plan Text" property="twitter:title"/>
        <meta content="width=device-width, initial-scale=1" name="viewport"/>
        <script type="text/javascript">!function(o,c){var n=c.documentElement,template=" w-mod-";n.className+=template+"js",("ontouchstart"in o||o.DocumentTouch&&c instanceof DocumentTouch)&&(n.className+=template+"touch")}(window,document);</script><link href="https://assets.website-files.com/603f193330681fd1b83bb639/603f193430681f2cda3bb75a_Favicon.png" rel="shortcut icon" type="image/x-icon"/>
        <link href="https://assets.website-files.com/603f193330681fd1b83bb639/603f193430681fbf6b3bb75b_webclip.png" rel="apple-touch-icon"/>
    </head>
    <body style = "margin: 0px;
    padding: 0px;">
        <div style = "margin: 0px; padding: 20px 5px; background-color: #fff;
        font-family: 'Trebuchet MS', 'Lucida Grande', 'Lucida Sans Unicode', 'Lucida Sans', Tahoma, sans-serif;
        color: #3b3f49;
        font-size: 17px;
        line-height: 1.4;">
            <!-- Change left-right padding "max-width" of grey box -->
            <div style = "max-width: 600px;
            margin-right: auto;
            margin-left: auto;
            border-radius: 20px;">
                <div style = "margin-bottom: 20px; text-align: center;">
                    <div>
                        <a href="https://atlasfinance.org" style = 'max-width:100%; display:inline-block '>
                            <img src="https://assets.website-files.com/603f193330681fd1b83bb639/603f1b47ad0ba6352587b0d0_Atlas%20Full%20Logo%20-%20Dark.png" height="50" sizes="157px" srcset="https://assets.website-files.com/603f193330681fd1b83bb639/603f1b47ad0ba6352587b0d0_Atlas%20Full%20Logo%20-%20Dark-p-500.png 500w, https://assets.website-files.com/603f193330681fd1b83bb639/603f1b47ad0ba6352587b0d0_Atlas%20Full%20Logo%20-%20Dark-p-800.png 800w, https://assets.website-files.com/603f193330681fd1b83bb639/603f1b47ad0ba6352587b0d0_Atlas%20Full%20Logo%20-%20Dark-p-1080.png 1080w, https://assets.website-files.com/603f193330681fd1b83bb639/603f1b47ad0ba6352587b0d0_Atlas%20Full%20Logo%20-%20Dark.png 1600w" alt=""/>
                        </a>
                    </div>
                </div>
                <!-- Change top-bottom padding "padding" of grey box -->
                <div style = 'margin-bottom: 2.4em; padding: 15px; border-radius: 15px; background-color: #f5f5f5;'>
                    <div style = "display: block;
                    max-width: 500px;
                    margin-right: auto;
                    margin-left: auto;">
                        <!--ALERT CONTENT GOES HERE-->
                        """
    template_end = """<div style = "height: 1px;
    margin-top: 30px;
    margin-bottom: 30px;
    background-color: #d1d5df;"></div>
    <p style = "font-size: 14px;
    color: #969caa;">Suggest new feedback and request new features on the <a href="http://forum.atlasfinance.org">Atlas Forum</a>.</p>
    </div>
    </div>
    <div style = "margin-bottom: 20px;">
    <div style = "text-align: center;">
    <div style = "font-size: 14px;
    color: #969caa;">Atlas Finance<strong></strong></div>
    <div style = "font-size: 14px;
    color: #969caa;">Proudly Based In Toronto</div>
    <div style = "margin-top: 20px;">
    <a href="https://dashboard.atlasfinance.org" target="_blank" style = "display: inline-block; margin-right: 5px; margin-left: 5px;
    padding: 5px 10px;
    border-radius: 5px;
    background-color: #f5f5f5;
    color: #969caa;
    font-size: 12px;
    text-decoration: none;">Manage Alerts</a>
    <a href="http://forum.atlasfinance.org" target="_blank" style = "display: inline-block; margin-right: 5px; margin-left: 5px;
    padding: 5px 10px;
    border-radius: 5px;
    background-color: #f5f5f5;
    color: #969caa;
    font-size: 12px;
    text-decoration: none;">Feedback</a>
    </div>
    </div>
    </div>
    </div>
    </div>
    <script src="https://d3e54v103j8qbb.cloudfront.net/js/jquery-3.5.1.min.dc5e7f18c8.js?site=603f193330681fd1b83bb639" type="text/javascript" integrity="sha256-9/aliU8dGd2tb6OSsuzixeV4y/faTqgFtohetphbbj0=" crossorigin="anonymous"></script>
    <script src="https://assets.website-files.com/603f193330681fd1b83bb639/js/webflow.16beae26e.js" type="text/javascript"></script><!--[if lte IE 9]><script src="//cdnjs.cloudflare.com/ajax/libs/placeholders/3.0.2/placeholders.min.js"></script><![endif]-->
    </body>
    </html>"""

    template_begin = template_begin.replace('{', '{{').replace('}', '}}')
    template_begin = template_begin.replace('for[', '{').replace(']mat', '}')

    template_end = template_end.replace('{', '{{').replace('}', '}}')
    template_end = template_end.replace('for[', '{').replace(']mat', '}')

    return template_begin, template_end


def generate_html(lines: list):
    """
    :param lines: list of tuples [(line_type, *args)]
    line types: (everything in square brackets is optional)
        - ('header', html_header_num, text)
        - ('title', text, ['small', 'medium', 'large'])
        - ('subtitle', text)
        - ('space', num_spaces)
        - ('data', data_name, data)
        - ('button', text, link)
    :return: str, html alert
    """
    alert_begin, alert_end = get_template()

    # Portion of the alert between required top and bottom
    alert_info = ''

    for line_type, *args in lines:
        if line_type == 'header':
            alert_info += f"""<h{args[0]}>{args[1]}</h{args[0]}>"""

        elif line_type == 'title':
            if len(args) < 2 or args[1] == 'medium':  # If size argument not given or ...
                # Medium size
                size = '136'
            elif args[1] == 'small':
                size = '128'
            elif args[1] == 'large':
                size = '150'
            else:
                raise KeyError('Invalid Title Size Given')

            alert_info += f"""<h1 style="font-size:{size}%;">{args[0]}</h1>"""

        elif line_type == 'subtitle':
            alert_info += f"""<p style="font-size:115%;">{args[0]}</p>"""

        elif line_type == 'space':
            alert_info += """\n<div style = "width: 16px; height: 12px;"></div>""" * args[0]

        elif line_type == 'data':
            if args[0]:
                alert_info += f"""\n<p style = "margin-bottom:8px;"><span style = "color: #3b3f49; font-weight: 700;">
                {args[0]}: </span>{args[1]}</p>"""
            else:
                alert_info += f"""\n<p style = "margin-bottom:8px;">{args[1]}</p>"""

        elif line_type == 'text':  # ('text', "Some Text!", size-%)
            if len(args) > 1:
                size = args[1]
            else:
                size = 100
            alert_info += f"""<p style="margin-bottom:8px;font-size:{size}%">{args[0]}</p>"""

        elif line_type == 'button':
            alert_info += f"""<a href="{args[1]}" style = "display: inline-block;
            min-width: 100px;
            padding: 8px 16px;
            border-style: solid;
            border-width: 1px;
            border-color: #0052ce;
            border-radius: 4px;
            background-color: #06f;
            color: #f5f5f5;
            font-size: 16px;
            font-weight: 700;
            display:inline-block;padding:9px 15px;
            color:white;border:0;line-height:inherit;text-decoration:none;cursor:pointer;">{args[0]} →</a>"""

        elif line_type == 'html':
            alert_info += args[0]

        else:
            raise KeyError('Invalid line type')

    alert = alert_begin + alert_info + alert_end

    return alert

def two_decimal(number, decimals=2, commas=False, prepend='', append='', factor=1):
    """Returns number in string format with 2 decimal points and with prepend and append
    - If a non-number is inputted, return the input"""
    try:
        number = float(number) * factor
    except:
        return number
    if number < 0 and prepend == '$':  # If this is a dollar format
        number *= (-1)  # Remove negative sign
        prepend = '-' + prepend  # Add negative sign before prepend

    elif prepend == '+':  # Change + to - if negative and remove if equals to 0, else keep it as +
        if number <= 0:
            prepend = ''  # '-' will be prepended automatically if negative

    return prepend + f"{{:{',' if commas else ''}.{decimals}f}}".format(number) + append
