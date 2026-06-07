from typing import *
from dataclasses import dataclass
from shared import cache
import json
from kb_builder.hparams_config import hpc
import pickle
from typing import *
from kb_builder.pre_processor.pdf_block import PDFBlock, PdfRegion
from shared.cache import mem
from bs4 import BeautifulSoup
from shared.pdf_parse_helper import load_pdf_page_as_image

def strip_tags_except_li(html_string):
    soup = BeautifulSoup(html_string, 'html.parser')
    tags_to_keep = ['li', 'p', 'div']
    
    # Convert all tags except 'li' to their text content
    for tag in soup.find_all(True):  # True matches all tags
        tag.attrs = {k:v for k, v in tag.attrs.items() if k == 'role' and v == 'img'}
        if tag.name not in tags_to_keep:
            # remove attributes from tag
            # for any block tags we need to add a <br/> to preserve the line breaks
            if tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                tag.insert_after(soup.new_tag('br'))
            tag.unwrap()
    return str(soup)

def local_marker_process_pdf(pdf_file_path: str) -> str:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered
    converter = PdfConverter(
        artifact_dict=create_model_dict(),
    )
    rendered = converter(pdf_file_path)
    text, _, images = text_from_rendered(rendered)
    return text

def marker_process_pdf_impl(pdf_file_path: str, marker_form_fields, wait_fixed_arg=2, stop_after_attempt_arg=3, max_polls=300, max_pages=None):
    import requests
    from kb_builder.dotenvvars import dotenvvars

    url = "https://www.datalab.to/api/v1/marker"


    headers = {"X-Api-Key": dotenvvars()['DATALAB_API_KEY']}
    from tenacity import retry, wait_fixed, stop_after_attempt
    @retry(wait=wait_fixed(wait_fixed_arg), stop=stop_after_attempt(stop_after_attempt_arg))
    def make_request():
        form_data = {
            'file': ('test.pdf', open(pdf_file_path, 'rb'), 'application/pdf'),
            **marker_form_fields
        }

        request_in_process = requests.post(url, files=form_data, headers=headers).json()
        if not ('success' in request_in_process and request_in_process['success']):
            print("error from marker", pdf_file_path, request_in_process)
            raise Exception(request_in_process)
        return request_in_process
    
    request_in_process = make_request()
    import time

    check_url = request_in_process["request_check_url"]

    for i in range(max_polls):
        time.sleep(2)
        response = requests.get(check_url, headers=headers).json()

        if response["status"] == "complete":
            break
    return response

    

def marker_process_pdf2(pdf_file_path, *args, **kwargs):
    if marker_process_pdf.check_call_in_cache(pdf_file_path):
        return marker_process_pdf.call(pdf_file_path)
    else:
        import hashlib
        file_hash = hashlib.md5(open(pdf_file_path, 'rb').read() + pickle.dumps([args, kwargs])).hexdigest()
        return cache.cached_call('marker_process_pdf2', file_hash, 
                                 lambda: marker_process_pdf_impl(pdf_file_path, *args, **kwargs))


@mem()
def marker_process_pdf(pdf_file_path: str) -> List[PDFBlock]:
    import requests
    from kb_builder.dotenvvars import dotenvvars

    url = "https://www.datalab.to/api/v1/marker"


    headers = {"X-Api-Key": dotenvvars()['DATALAB_API_KEY']}
    from tenacity import retry, wait_fixed, stop_after_attempt
    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
    def make_request():
        form_data = {
            'file': ('test.pdf', open(pdf_file_path, 'rb'), 'application/pdf'),
            "use_llm": (None, hpc().marker_endpoint_params.use_llm),
            "force_ocr": (None, hpc().marker_endpoint_params.force_ocr),
            "paginate": (None, True),
        }

        request_in_process = requests.post(url, files=form_data, headers=headers).json()
        if not ('success' in request_in_process and request_in_process['success']):
            print("error from marker", pdf_file_path, request_in_process)
            raise Exception(request_in_process)
        return request_in_process
    
    request_in_process = make_request()
    import time

    max_polls = 300
    check_url = request_in_process["request_check_url"]

    for i in range(max_polls):
        time.sleep(2)
        response = requests.get(check_url, headers=headers).json() # Don't forget to send the auth headers

        if response["status"] == "complete":
            break
    md = response['markdown']

    return parse_pdf_markdown(md)

    # def iter_obj(obj):
    #     for value in obj['children']:
    #         if 'children' in value and value['children'] is not None:
    #             if 'block_type' in value:
    #                 yield value['block_type']
    #             print('recurs')
    #             yield from iter_obj(value)
    #         else:
    #             yield PDFBlock(value['block_type'])
    

def parse_pdf_markdown(markdown_text: str) -> List[PDFBlock]:
    """
    Parses markdown text with page break markers into a list of PDFBlock objects.

    Args:
        markdown_text: The markdown text to parse.

    Returns:
        A list of PDFBlock objects.
    """
    import re
    regex = r"{(\d+)}------------------------------------------------"
    blocks: List[PDFBlock] = []
    current_page_number: Optional[int] = None
    current_text_lines: List[str] = []

    lines = markdown_text.splitlines()

    for line in lines:
        match = re.match(regex, line)
        if match:
            page_num = int(match.group(1))
            if current_page_number is not None:
                # Save the previous block
                blocks.append(PDFBlock(text="\n".join(current_text_lines).strip(), region=PdfRegion(page_number=current_page_number)))
            current_page_number = page_num
            current_text_lines = [] # Reset text for the new page
        else:
            current_text_lines.append(line)

    # Add the last block after the last page marker
    if current_page_number is not None:
        text = "\n".join(current_text_lines).strip()
        blocks.append(PDFBlock(text=text, region=PdfRegion(page_number=current_page_number)))
    return blocks

@mem()
def cached_marker_process_to_json(pdf_file_path: str, marker_form_fields, wait_fixed_arg=2, stop_after_attempt_arg=3, max_polls=300, max_pages=None):
    import requests
    from kb_builder.dotenvvars import dotenvvars

    url = "https://www.datalab.to/api/v1/marker"


    headers = {"X-Api-Key": dotenvvars()['DATALAB_API_KEY']}
    from tenacity import retry, wait_fixed, stop_after_attempt
    @retry(wait=wait_fixed(wait_fixed_arg), stop=stop_after_attempt(stop_after_attempt_arg))
    def make_request():
        form_data = {
            'file': ('test.pdf', open(pdf_file_path, 'rb'), 'application/pdf'),
            **marker_form_fields
        }

        request_in_process = requests.post(url, files=form_data, headers=headers).json()
        if not ('success' in request_in_process and request_in_process['success']):
            print("error from marker", pdf_file_path, request_in_process)
            raise Exception(request_in_process)
        return request_in_process
    
    request_in_process = make_request()
    import time

    check_url = request_in_process["request_check_url"]

    for i in range(max_polls):
        time.sleep(2)
        response = requests.get(check_url, headers=headers).json()

        if response["status"] == "complete":
            break
    return response


@mem()
def cached_marker_process_to_json_non_pdf(file_path: str, format: str, marker_form_fields, wait_fixed_arg=2, stop_after_attempt_arg=3, max_polls=300, max_pages=None):
    import requests

    url = "https://www.datalab.to/api/v1/marker"

    headers = marker_headers()
    from tenacity import retry, wait_fixed, stop_after_attempt
    @retry(wait=wait_fixed(wait_fixed_arg), stop=stop_after_attempt(stop_after_attempt_arg))
    def make_request():
        form_data = {
            'file': (f'test', open(file_path, 'rb'), format),
            **marker_form_fields
        }

        request_in_process = requests.post(url, files=form_data, headers=headers).json()
        if not ('success' in request_in_process and request_in_process['success']):
            print("error from marker", file_path, request_in_process)
            raise Exception(request_in_process)
        return request_in_process
    
    request_in_process = make_request()

    check_url = request_in_process["request_check_url"]
    return wait_for_marker_to_complete(max_polls, check_url, headers)

def marker_headers():
    from kb_builder.dotenvvars import dotenvvars
    return {"X-Api-Key": dotenvvars()['DATALAB_API_KEY']}

def wait_for_marker_to_complete(max_polls, check_url, headers):
    import time
    import requests
    for i in range(max_polls):
        time.sleep(2)
        response = requests.get(check_url, headers=headers).json()

        if response["status"] == "complete":
            break
    return response

# Helper function to extract a PdfRegion from a block’s bounding box (bbox).
def get_region_from_bbox(bbox: Optional[List[float]], page_number: int, page_bbox, img_url: Optional[str] = None) -> PdfRegion:
    if bbox and len(bbox) == 4:
        page_width = page_bbox[2]
        page_height = page_bbox[3]
        x0, y0, x1, y1 = bbox
        x0 /= page_width
        x1 /= page_width
        y0 /= page_height
        y1 /= page_height
        return PdfRegion(
            page_number=page_number,
            horizontal_position=x0,
            vertical_position=y0,
            width=x1 - x0,
            height=y1 - y0,
            image_url=img_url
        )
    return PdfRegion(page_number=page_number, image_url=img_url)

# Recursive function that walks the tree for one block and returns all leaf PDFBlocks.
def flatten_leaf_blocks(block: Dict[str, Any], page_number: int, page_bbox) -> List[PDFBlock]:
    blocks: List[PDFBlock] = []
    assert block.get('block_type') not in ['Table', 'TableGroup', 'FigureGroup', 'PictureGroup', 'Figure', 'Picture'], f'unexpected block type: {block.get("block_type")}\n\nblock: {block}'
    # If the block has children, process them instead of (or in addition to) the container.
    if block.get("children"):
        for child in block["children"]:
            blocks.extend(flatten_leaf_blocks(child, page_number, page_bbox))
    else:
        # For a leaf node, get its HTML text.
        html_content = block.get("html", "").strip()
        html_content = strip_tags_except_li(html_content)
        if html_content:
            region = get_region_from_bbox(block.get("bbox"), page_number, page_bbox)
            blocks.append(PDFBlock(text=html_content, type=block.get('block_type'), region=region))
    return blocks


# Main function: given Marker’s JSON (a list where each item is a page block),
# iterate over pages and flatten the children into PDFBlocks.
def marker_json_to_pdf_blocks(marker_json: List[Dict[str, Any]], pdf_path: str) -> List[PDFBlock]:
    import json
    open('/tmp/marker.json', 'w').write(json.dumps(marker_json, indent=2))
    # open('/tmp/marker_json.json', 'w').write(json.dumps(marker_json, indent=2))
    pdf_blocks: List[PDFBlock] = []
    # If mini_run is enabled, only process the first page
    pages_to_process = marker_json[:1] if hpc().mini_run else marker_json
    for page_index, page in enumerate(pages_to_process):
        assert page['id'].startswith(f'/page/{page_index}')
        page_number = page_index + 1
        page_bbox = page['bbox']
        # Each page block is a container.
        # (You could also process the page-level block if needed; here we assume that
        # the “real” text is contained in its children.)
        if "children" in page and page["children"]:
            for child in page["children"]:
                block_type = child['block_type']
                def add_block(html, img_url=None):
                    pdf_blocks.append(PDFBlock(text=html, type=block_type, region=get_region_from_bbox(child['bbox'], page_number, page_bbox, img_url)))

                if block_type == 'Table':
                    add_block(child['html'])
                elif block_type == 'TableGroup':
                    html = '\n'.join([c['html'] for c in child['children']])
                    add_block(html)
                elif block_type in ['Picture', 'Figure', 'Form', 'FigureGroup', 'PictureGroup']:
                    if block_type.endswith('Group'):
                        html = '\n'.join([c['html'] for c in child['children']])
                    else:
                        html = child['html']
                    img_url = load_pdf_page_as_image(pdf_path, page_number, bbox=child['bbox'], page_bbox=page_bbox)
                    add_block(html, img_url)
                else:
                    pdf_blocks.extend(flatten_leaf_blocks(child, page_number, page_bbox))
    return pdf_blocks

def json_marker_process_pdf(pdf_file_path: str, format: str) -> str:
    marker_form_fields = {
        "use_llm": (None, hpc().marker_endpoint_params.use_llm),
        "force_ocr": (None, hpc().marker_endpoint_params.force_ocr),
        "paginate": (None, True),
        'output_format': (None, 'json'),
        'disable_image_extraction': (None, hpc().enable_marker_describe_image)
    }
    if format == 'application/pdf':
        obj = marker_process_pdf2(pdf_file_path, marker_form_fields)
        # if obj['json'] is None:
        #     print("retrying marker process")
        #     obj = cached_marker_process_to_json.call(pdf_file_path, marker_form_fields)

    else:
        obj = cached_marker_process_to_json_non_pdf(pdf_file_path, format, marker_form_fields)
    if type(obj) == tuple:
        print("obj is a tuple", obj)
    return obj['json']

def marker_blocks_using_json(pdf_file_path: str, format='application/pdf') -> List[PDFBlock]:
    marker_json = json_marker_process_pdf(pdf_file_path, format)
    print("got marker json")
    return marker_json_to_pdf_blocks(marker_json['children'], pdf_file_path)
    