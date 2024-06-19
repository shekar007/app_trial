# %%
import sys
import os
import shutil
import subprocess
import sys
import os
import bs4.element
import yaml
import re
import os
import pypandoc
from collections import OrderedDict
from bs4 import BeautifulSoup
import re
import os
import time
import shutil
import re
from enum import Enum
import sys
import difflib
from diff_match_patch import diff_match_patch
import diff_match_patch as dmp_module

import os

def clean_pycache():
    """Clean __pycache__ directories recursively."""
    for root, dirs, files in os.walk(".", topdown=False):
        for name in dirs:
            if name == "__pycache__":
                pycache_dir = os.path.join(root, name)
                # # print(f"Deleting {pycache_dir}")
                shutil.rmtree(pycache_dir)


# Define the exact strings to remove

def remove_conditional_comments(input):
    
    strings_to_remove = [
        '<!--[if IE 8]><html class="no-js lt-ie9" lang="en" > <![endif]-->',
        '<!--[if gt IE 8]><!--> <html class="no-js" lang="en" > <!--<![endif]-->'
    ]

    # Remove the specified strings
    for string in strings_to_remove:
        input = input.replace(string, '')
    return input


def apply_diff_match_patch(input1, input2):
    dmp = dmp_module.diff_match_patch()
    diff = dmp.diff_main(input1,
                            input2,
                            0)
    dmp.diff_cleanupSemantic(diff)
    return diff

def find_first_unmatched_gt(text, open_global, close_global):
    open =0
    close = 0
    for i, char in enumerate(text):
        if char == '<':
            open_global += 1
            open+=1
        elif char == '>':
            close_global += 1
            close +=1
            if close > open:
                return i, open_global, close_global
    return -1, open_global, close_global

def add_highlight_to_first_unmatched_gt(text, open_count, close_count, color):
    pos, open_count, close_count = find_first_unmatched_gt(text, open_count, close_count)
    if pos != -1:
        text = text[:pos] + f' class="highlight-{color}"' + text[pos:]
    return text, open_count, close_count

def highlight_balanced_html_substrings(html, open_count, close_count, color):
    str = ""
    highlighted_html = []
    in_span = False
    prev = False
    for i, char in enumerate(html):
        if(char == '<'):
            open_count+=1
        elif (char == '>'):
            close_count+=1
        if(open_count == close_count):
            
            if(not prev):
                if(char == '>'):
                    str +=char
                    highlighted_html.append(str)
                    prev = False
                    str = ""
                    continue
                if(len(str) and (not str.isspace())):
                    highlighted_html.append(str)
            str+= char
            prev = True
            if(i == len(html)-1):
                if(len(str) != 0 and (not str.isspace())):
                    highlighted_html.append(f'<span class="highlight-{color}">')
                    highlighted_html.append(str)
                    highlighted_html.append('</span>')
                    str = ""
        else :
            
            if(prev):
                
                if(len(str) != 0 and (not str.isspace())):
                    highlighted_html.append(f'<span class="highlight-{color}">')
                    highlighted_html.append(str)
                    highlighted_html.append('</span>')
                    str = ""
            str+=char
            prev = False
            if(i == len(html)-1):
                if(len(str) != 0 and (not str.isspace())):
                    highlighted_html.append(str)
                    str = ""
    return ''.join(highlighted_html), open_count, close_count


def add_class_to_matching_tags(html, color):
    # Function to add class to matched opening and closing tags
    def replacer(match):
        opening_tag = match.group(1)
        tag_name = match.group(2)
        attributes = match.group(3)
        content = match.group(4)
        closing_tag = match.group(5)
        
        # Add class to the opening tag based on the color input
        new_opening_tag = f'<{tag_name}{attributes} class="highlight-{color}">'
        
        return f'{new_opening_tag}{content}{closing_tag}'

    # Regex pattern to match tags with their corresponding closing tags
    pattern = r'(<(\w+)([^>]*)>)(.*?)(<\/\2>)'
    
    # Perform the substitution with the replacer function
    modified_html = re.sub(pattern, replacer, html, flags=re.DOTALL)
    
    return modified_html





def filter_diffs(diff):
    array_1 = []
    array_2 = []

    for key, value in diff:
        if key in [-1, 0]:
            array_1.append((key, value))
        if key in [1, 0]:
            array_2.append((key, value))
    return array_1, array_2

    
def remove_class_from_closing_tags(html):
    pattern = re.compile(r'(</[^ >]+)[^>]*>')
    return pattern.sub(lambda m: f'{m.group(1)}>', html)

def remove_nested_highlight(html, color):
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all elements with class 'highlight-pink'
    highlight_pink_elements = soup.find_all(class_=f'highlight-{color}')
    
    for element in highlight_pink_elements:
        # Find all span elements with class 'highlight-pink' within the current element
        span_elements = element.find_all('span', class_=f'highlight-{color}')
        
        for span in span_elements:
            # Replace the span element with its contents
            span.unwrap()
    
    return str(soup)


def add_conditional_comments(html_content):
    
    # Define the conditional comments to be inserted
    conditional_comments = '''<!--[if IE 8]><html class="no-js lt-ie9" lang="en" > <![endif]-->
    <!--[if gt IE 8]><!--> <html class="no-js" lang="en" > <!--<![endif]-->'''

    # Find the position of <!DOCTYPE html>
    doctype_position = html_content.find('<!DOCTYPE html>') + len('<!DOCTYPE html>')

    # Insert the conditional comments after <!DOCTYPE html>
    modified_html_content = html_content[:doctype_position] + '\n' + conditional_comments + html_content[doctype_position:]
    return modified_html_content

def add_button(soup, color) :
    
    # Create the button element with styles and JavaScript
    button_html = f'''
    <button id="scrollButton" style="position: fixed; bottom: 20px; right: 20px; padding: 10px 20px; background-color: {'#ff69b4' if color == 'pink' else '#90ee90'}; color: white; border: none; border-radius: 5px; cursor: pointer;">
        Scroll to Highlight
    </button>
    <script>
        let currentHighlightIndex = 0;
        const highlightElements = Array.from(document.querySelectorAll('.highlight-{color}'));

        function isElementInViewport(el) {{
            const rect = el.getBoundingClientRect();
            return (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                rect.right <= (window.innerWidth || document.documentElement.clientWidth)
            );
        }}

        document.getElementById('scrollButton').addEventListener('click', function() {{
            let foundNextElement = false;

            for (let i = 0; i < highlightElements.length; i++) {{
                currentHighlightIndex = (currentHighlightIndex + 1) % highlightElements.length;
                if (!isElementInViewport(highlightElements[currentHighlightIndex])) {{
                    const highlightElement = highlightElements[currentHighlightIndex];
                    const elementTop = highlightElement.getBoundingClientRect().top;
                    const elementHeight = highlightElement.getBoundingClientRect().height;
                    const viewportHeight = window.innerHeight;
                    const offset = elementTop + window.scrollY - (viewportHeight / 2) + (elementHeight / 2);

                    window.scrollTo({{
                        top: offset,
                        behavior: 'smooth'
                    }});

                    foundNextElement = true;
                    break;
                }}
            }}

            if (!foundNextElement) {{
                alert('All highlighted texts are in view.');
            }}
        }});
    </script>
    '''
    button_soup = BeautifulSoup(button_html, 'html.parser')

    # Insert the button before the closing </body> tag
    body_tag = soup.find('body')
    if body_tag:
        body_tag.append(button_soup)

def add_style(soup, color):
    # Add the additional styles for .highlight-pink
    style_tag = soup.new_tag('style')
    if color == 'pink':
        style_tag.string = '''
            /* Define the highlight-pink style */
.highlight-pink {
    background-color: rgba(255, 192, 203, 0.5); /* Light pink with 50% transparency */
    padding: 0.2em; /* Add some padding for better visibility */
    border-radius: 0.2em; /* Optional: rounded corners */
    animation: highlight-pink 2s infinite; /* Apply the highlight-pink animation */
}

/* Define the animation keyframes for highlight-pink */
@keyframes highlight-pink {
    0% {
        background-color: rgba(255, 192, 203, 0.5);
    }
    50% {
        background-color: rgba(255, 128, 171, 0.8); /* Darker pink */
    }
    100% {
        background-color: rgba(255, 192, 203, 0.5);
    }
}
        '''
    elif color == 'green':
        style_tag.string = '''

/* Define the highlight-green style */
.highlight-green {
    background-color: rgba(144, 238, 144, 0.5); /* Light green with 50% transparency */
    padding: 0.2em; /* Add some padding for better visibility */
    border-radius: 0.2em; /* Optional: rounded corners */
    animation: highlight-green 2s infinite; /* Apply the highlight-green animation */
}
/* Define the animation keyframes for highlight-green */
@keyframes highlight-green {
    0% {
        background-color: rgba(144, 238, 144, 0.5);
    }
    50% {
        background-color: rgba(173, 216, 130, 0.8); /* Lighter green */
    }
    100% {
        background-color: rgba(144, 238, 144, 0.5);
    }
}

        '''
    head_tag = soup.find('head')
    if head_tag:
        head_tag.append(style_tag)

def store_and_write(output_left, output_right, left_file_path, right_file_path, diff_file):
    # Generate left and right paths
    # Copy left file
    with open(left_file_path, "w") as file :
        file.write(output_left)

    # Copy right file
    
    with open(right_file_path, "w") as file :
        file.write(output_right)

    return left_file_path, right_file_path
    
        

def classCorrector(input):
    
# Define the regular expression pattern
    pattern = r'<(\w+)\s*class\s*=\s*"([^"]*?)"\s*class\s*=\s*"([^"]*?)"\s*>(.*?)<\/\1>'

    # Define the replacement pattern
    replacement = r'<\1 class="\2 \3">\4</\1>'
    html_output = re.sub(pattern, replacement, input, flags=re.DOTALL)
    return html_output



def changes(input1, input2):
    diff = apply_diff_match_patch(input1, input2)
    # # print(diff)
    # # print()
    # # print()
    array_1, array_2 = filter_diffs(diff)
    highlighted_array_1_pink = []
    open_count = 0
    close_count = 0

    prev = 2
    for key, value in array_1:
        # # print("original value :")
        # # print(value)
        modified_value = value
        if key == -1:
            # Add the highlight class to all opening tags with matching closing tags
            modified_value = add_class_to_matching_tags(modified_value, "pink")
        if(prev == -1):
            modified_value, open_count, close_count = add_highlight_to_first_unmatched_gt(modified_value, open_count, close_count, "pink")
        else:
            open_count += len(re.findall(r'<', value))
            close_count+= len(re.findall('>', value))
        highlighted_array_1_pink.append((key, modified_value))
        if(key == -1):
            prev = -1
        # # print("modified value")
        # # print(modified_value)

    open_count = 0
    close_count = 0

    highlighted_array_2_pink = []
    for key, value in highlighted_array_1_pink:

        modified_value = value
        if key == -1:
            modified_value, open_count, close_count = highlight_balanced_html_substrings(modified_value, open_count, close_count, "pink")
        else:
            open_count += len(re.findall(r'<', value))
            close_count+= len(re.findall('>', value))

        highlighted_array_2_pink.append((key, modified_value))


    highlighted_html_1_pink = ''.join(value for _, value in highlighted_array_2_pink)
    after_merge_pink = classCorrector(highlighted_html_1_pink)
    cleaned_html_pink = remove_class_from_closing_tags(after_merge_pink)
    html_after_processing_pink = remove_nested_highlight(cleaned_html_pink, "pink")
    ### print(html_after_processing_pink)
    ## print()
    highlighted_array_1_green = []
    open_count = 0
    close_count = 0

    prev = 2
    for key, value in array_2:
        modified_value = value
        if key == 1:
            # Add the highlight class to all opening tags with matching closing tags
            modified_value = add_class_to_matching_tags(modified_value, "green")
        if(prev == 1):
            modified_value, open_count, close_count = add_highlight_to_first_unmatched_gt(modified_value, open_count, close_count, "green")
        else:
            open_count += len(re.findall(r'<', value))
            close_count+= len(re.findall('>', value))
        highlighted_array_1_green.append((key, modified_value))
        if(key == 1):
            prev = 1

    open_count = 0
    close_count = 0

    highlighted_array_2_green = []
    for key, value in highlighted_array_1_green:

        modified_value = value
        if key == 1:
            modified_value, open_count, close_count = highlight_balanced_html_substrings(modified_value, open_count, close_count, "green")
        else:
            open_count += len(re.findall(r'<', value))
            close_count+= len(re.findall('>', value))

        highlighted_array_2_green.append((key, modified_value))
        
    
    highlighted_html_1_green = ''.join(value for _, value in highlighted_array_2_green)
    after_merge_green = classCorrector(highlighted_html_1_green)
    cleaned_html_green = remove_class_from_closing_tags(after_merge_green)
    html_after_processing_green = remove_nested_highlight(cleaned_html_green, "green")
    ## print(html_after_processing_green)
    ## print()
    return html_after_processing_pink, html_after_processing_green
    # Parse the modified HTML content with BeautifulSoup


def soupify(input1, input2, left_file_path, right_file_path, output_path):
    
    input1 = add_conditional_comments(input1)
    input2 = add_conditional_comments(input2)
    input1 = BeautifulSoup(input1, 'html.parser')
    add_button(input1,"pink")

    add_style(input1, "pink")
    input2 = BeautifulSoup(input2, 'html.parser')
    
    add_button(input2,"green")

    add_style(input2, "green")

    input1 = str(input1)
    input2 = str(input2)
    return store_and_write(input1, input2, left_file_path, right_file_path, output_path)


import os

def get_relative_path(from_path, to_path):
    """
    Compute the relative path from from_path to to_path.
    """
    # Convert both paths to absolute paths
    from_path_abs = os.path.abspath(from_path)
    to_path_abs = os.path.abspath(to_path)

    # Compute the relative path
    relative_path = os.path.relpath(to_path_abs, os.path.dirname(from_path_abs))

    return relative_path

def generate_comparison_html(left_html, right_html, output_path):
    """
    Generate a comparison HTML file with embedded content from left_html and right_html.
    """
    leftpath = get_relative_path(output_path, left_html)
    rightpath = get_relative_path(output_path, right_html)

    # Check if rightpath exists
    if not os.path.exists(right_html):
        rightpath = "data:text/html,<html><body><h1 class='message'>File on the Right was Deleted</h1></body></html>"

    comparison_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comparison Webpages</title>
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            height: 100%;
            overflow: hidden; /* Hide body overflow */
            font-family: Arial, sans-serif;
        }}
        .container {{
            display: flex;
            height: 100%;
            overflow: hidden; /* Hide container overflow */
        }}
        .iframe-container {{
            flex: 1;
            height: 100%;
            position: relative; /* Position relative for absolute positioning */
            border: 2px solid #ccc; /* Border style */
            border-radius: 5px; /* Rounded border */
            overflow: hidden; /* Hide overflow to prevent scrollbars */
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
            position: absolute; /* Position iframe absolutely */
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            overflow: auto; /* Allow iframe content scrolling */
            -ms-overflow-style: none;  /* Hide scrollbar for IE and Edge */
            scrollbar-width: none;  /* Hide scrollbar for Firefox */
        }}
        iframe::-webkit-scrollbar {{
            display: none;  /* Hide scrollbar for Chrome, Safari, and Opera */
        }}
        .message {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100%;
            font-size: 2rem;
            color: #fff;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
            background: linear-gradient(135deg, #ff6347, #ff4500);
        }}
        .file-added {{
            background: linear-gradient(135deg, #32cd32, #228b22);
        }}
        .file-deleted {{
            background: linear-gradient(135deg, #ff4500, #b22222);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="iframe-container" id="left-iframe-container">
            <iframe id="left-iframe" src="{leftpath}"></iframe>
        </div>
        <div class="iframe-container" id="right-iframe-container">
            <iframe id="right-iframe" src="{rightpath}"></iframe>
        </div>
    </div>
    <script>
        function setupIframeNavigation() {{
            const leftIframeContainer = document.getElementById('left-iframe-container');
            const rightIframeContainer = document.getElementById('right-iframe-container');
            const leftIframe = leftIframeContainer.querySelector('iframe');
            const rightIframe = rightIframeContainer.querySelector('iframe');

            leftIframe.addEventListener('load', function() {{
                const iframeDocument = leftIframe.contentDocument || leftIframe.contentWindow.document;
                
                iframeDocument.addEventListener('click', function(event) {{
                    handleLinkClick(event, leftIframeContainer, rightIframeContainer, leftIframe, rightIframe);
                }});
            }});
            
            rightIframe.addEventListener('load', function() {{
                const iframeDocument = rightIframe.contentDocument || rightIframe.contentWindow.document;
                
                iframeDocument.addEventListener('click', function(event) {{
                    handleLinkClick(event, rightIframeContainer, leftIframeContainer, rightIframe, leftIframe);
                }});
            }});
        }}

        function handleLinkClick(event, clickedIframeContainer, otherIframeContainer, clickedIframe, otherIframe) {{
            const link = event.target.closest('a');
            if (link) {{
                event.preventDefault();
                const newUrl = link.getAttribute('href');

                // Check if the link is external
                if (new URL(newUrl, window.location.href).origin !== window.location.origin) {{
                    // Open external links in a new tab
                    window.open(newUrl, '_blank');
                    console.log("external link");
                }} else if (newUrl.startsWith('#')) {{
                    // Handle anchor links within the same iframe
                    const anchor = newUrl.substring(1);
                    const element = clickedIframe.contentDocument.getElementById(anchor) || clickedIframe.contentDocument.getElementsByName(anchor)[0];
                    if (element) {{
                        scrollToElement(element, clickedIframe);
                    }}
                    console.log("anchor link");
                }} else {{
                    // Check if the new URL exists in the file system
                    fetch(newUrl, {{ method: 'HEAD' }})
                        .then(response => {{
                            if (response.ok) {{
                                // URL exists
                                otherIframeContainer.style.display = 'none';
                                clickedIframe.src = newUrl;
                                console.log("internal link exists");
                            }} else {{
                                // URL does not exist
                                handleMissingFile(otherIframeContainer, newUrl);
                            }}
                        }})
                        .catch(error => {{
                            // Error handling
                            console.error('Error:', error);
                            handleMissingFile(otherIframeContainer, newUrl);
                        }});
                }}
            }}
        }}

        function handleMissingFile(container, url) {{
            const isRightContainer = container.id === 'right-iframe-container';
            if (isRightContainer) {{
                // Display "File Deleted" in the right iframe
                container.querySelector('iframe').src = 'data:text/html,<html><body><h1 class="message">File on the Left has been deleted</h1></body></html>';
                console.log("file deleted");
            }} else {{
                // Display "File Added" in the left iframe
                container.querySelector('iframe').src = 'data:text/html,<html><body><h1 class="message file-added">File on the Right was Added</h1></body></html>';
                console.log("file added");
            }}
        }}

        function scrollToElement(element, iframe) {{
            const rect = element.getBoundingClientRect();
            const iframeRect = iframe.getBoundingClientRect();
            const offsetX = rect.left - iframeRect.left + iframe.contentWindow.pageXOffset;
            const offsetY = rect.top - iframeRect.top + iframe.contentWindow.pageYOffset;
            
            iframe.contentWindow.scrollTo({{ left: offsetX, top: offsetY, behavior: 'smooth' }});
        }}

        // Setup navigation for both iframes
        setupIframeNavigation();
    </script>
</body>
</html>"""
    # Save the comparison HTML to the output directory
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(comparison_html)
    print(f"Comparison HTML saved to: {output_path}")


def create_union_folder(left_folder, right_folder, union_folder_name):
    """
    Create a union folder structure without copying contents.
    """
    # Create union folder in the current directory
    union_folder = os.path.join(os.getcwd(), union_folder_name)
    os.makedirs(union_folder, exist_ok=True)

    # Create union folder structure from left_folder
    for root, dirs, _ in os.walk(left_folder):
        for d in dirs:
            src_dir = os.path.join(root, d)
            dest_dir = os.path.join(union_folder, os.path.relpath(src_dir, left_folder))
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
    
    # Create union folder structure from right_folder
    for root, dirs, _ in os.walk(right_folder):
        for d in dirs:
            src_dir = os.path.join(root, d)
            dest_dir = os.path.join(union_folder, os.path.relpath(src_dir, right_folder))
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
    
    return union_folder


def diff_html(left_file, right_file, output_path):
    
    with open(left_file, "r") as file:
        left_file_content = file.read()
    with open(right_file, "r") as file:
        right_file_content = file.read()    
    
    input1 = remove_conditional_comments(left_file_content)
    input2 = remove_conditional_comments(right_file_content)

    output1, output2 = changes(input1, input2)
    
    leftpath, rightpath = soupify(output1, output2, left_file, right_file, output_path)

    generate_comparison_html(leftpath, rightpath, output_path)
    # print()
    # print("you can open it from the comparison.html in the directory same as the path that you gave us on the command line")
        

def handle_left_only(left_path, output_path):
    storepath = get_relative_path(output_path, left_path)
    print("")
    with open(left_path, "r") as file:
        input = file.read()
    soup = BeautifulSoup(input, "html.parser")
    add_button(soup,"pink")

    add_style(soup, "pink")

    with open(left_path, "w") as file:
        file.write(str(soup))
    
    comparison_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comparison Webpages</title>
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            height: 100%;
        }}
        .container {{
            display: flex;
            height: 100%;
        }}
        .iframe-container {{
            flex: 1;
            height: 100%;
            overflow-y: auto;
            overflow-x: auto;
            border: 1px solid #ccc;
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
        .file-deleted {{
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            height: 100%;
            color: red;
            font-size: 2em;
            border: 1px solid #ccc;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="iframe-container">
            <iframe src="{storepath}"></iframe>
        </div>
        <div class="iframe-container">
            <div class="file-deleted">File on the Left has been Deleted</div>
        </div>
    </div>
</body>
</html>"""
    with open(output_path, "w") as file:
        file.write(comparison_html)
    
    
    

def handle_right_only(right_path, output_path):
    storepath = get_relative_path(output_path, right_path)
    with open(right_path, "r") as file:
        input = file.read()
    soup = BeautifulSoup(input, "html.parser")
    add_button(soup,"green")

    add_style(soup, "green")

    with open(right_path, "w") as file:
        file.write(str(soup))
    
    left_message = "The File on the Right has been Added"
    comparison_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comparison Webpages</title>
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            height: 100%;
        }}
        .container {{
            display: flex;
            height: 100%;
        }}
        .iframe-container {{
            flex: 1;
            height: 100%;
            overflow-y: auto;
            overflow-x: auto;
            border: 1px solid #ccc;
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
        .file-added {{
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            height: 100%;
            color: green;
            font-size: 2em;
            border: 1px solid #ccc;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="iframe-container">
            <div class="file-added">{left_message}</div>
        </div>
        <div class="iframe-container">
            <iframe src="{storepath}"></iframe>
        </div>
    </div>
</body>
</html>"""
    with open(output_path, "w") as file:
        file.write(comparison_html)
    
def traverse_and_diff(left_folder, right_folder, merged_folder):
    """
    Recursively traverse folders, find HTML files, and compare them.
    """
    def traverse_and_collect(folder, is_left, file_dict):
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, folder)
                    if is_left:
                        file_dict[relative_path] = (file_path, None)
                    else:
                        if relative_path in file_dict:
                            file_dict[relative_path] = (file_dict[relative_path][0], file_path)
                        else:
                            file_dict[relative_path] = (None, file_path)

    file_dict = {}
    traverse_and_collect(left_folder, True, file_dict)
    traverse_and_collect(right_folder, False, file_dict)

    for relative_path, (left_file, right_file) in file_dict.items():
        output_file = os.path.join(merged_folder, relative_path)
        output_file_abs = os.path.abspath(output_file)

        if left_file:
            left_file_abs = os.path.abspath(left_file)
        if right_file:
            right_file_abs = os.path.abspath(right_file)

        if left_file and right_file:
            diff_html(left_file_abs, right_file_abs, output_file_abs)
        elif left_file and not right_file:
            handle_left_only(left_file_abs, output_file_abs)
        elif not left_file and right_file:
            handle_right_only(right_file_abs, output_file_abs)

def main():
    # Clean __pycache__ before running the main code
    clean_pycache()
    # Check if the correct number of arguments are provided
    if len(sys.argv) != 3:
        print("Usage: python3 difference.py <left_directory_path> <right_directory_path>")
        sys.exit(1)
    left_directory_path = sys.argv[1]
    right_directory_path = sys.argv[2]
    copy_folder = 'copy_folder'
    diff_folder = 'diff_folder'
 # Ensure the copy_folder exists
    if not os.path.exists(copy_folder):
        os.makedirs(copy_folder)
    if not os.path.exists(diff_folder):
        os.makedirs(diff_folder)
    # Define paths for the copied directories inside copy_folder
    left_copy_path = os.path.join(copy_folder, 'left')
    right_copy_path = os.path.join(copy_folder, 'right')
    
    # Copy the left directory
    if os.path.exists(left_copy_path):
        shutil.rmtree(left_copy_path)  # Remove if it already exists
    shutil.copytree(left_directory_path, left_copy_path)
    
    # Copy the right directory
    if os.path.exists(right_copy_path):
        shutil.rmtree(right_copy_path)  # Remove if it already exists
    shutil.copytree(right_directory_path, right_copy_path)
    
    diff_folder = create_union_folder(left_copy_path, right_copy_path, diff_folder)
    ## print("Union folder created at:", diff_folder)
    traverse_and_diff(left_copy_path, right_copy_path, diff_folder)

    

if __name__ == "__main__":
    main()
# %%
