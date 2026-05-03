import pymupdf

# Settings
MARGIN = 20

def add_stamp(input_pdf, output_pdf, stamp_path, pages_to_stamp=None):
  # Open the pdf with pymupdf.
  doc = pymupdf.open(input_pdf)

  # Pages not specified, default to all pages.
  if pages_to_stamp == None:
    pages_to_stamp = range(1, len(doc) + 1)
  
  # Define where the stamp goes (x0, y0, x1, y1)
  # This example places it in a 100x100 square at the top right
  stamp_width = 192
  stamp_height = 53

  for page_num in pages_to_stamp:
    # PDF page indices start at 0
    page = doc[page_num - 1]
    
    # Obtain page dimensions.
    br = page.rect.br
    # x0 = 612 - 192 - 20 = 400
    # y0 = 792 - 53 - 20 = 719
    # x1 = 612 - 20 = 592
    # y1 = 792 - 20 = 772
    x0 = br.x - stamp_width - MARGIN
    y0 = br.y - stamp_height - MARGIN
    x1 = br.x - MARGIN
    y1 = br.y - MARGIN
    temp_rect = pymupdf.Rect(x0, y0, x1, y1)

    # CHECK FOR TEXT: search for any text inside that rectangle
    text_in_rect = page.get_text("text", clip=temp_rect)

    # There is text in the way, move up.
    temp_y0 = y0
    temp_y1 = y1
    while text_in_rect.strip() and temp_y0 > 0:
      temp_y0 = temp_y0 - MARGIN
      temp_y1 = temp_y1 - MARGIN
      temp_rect = pymupdf.Rect(x0, temp_y0, x1, temp_y1)
      text_in_rect = page.get_text("text", clip=temp_rect)
    
    # Went out of bounds, default to bottom right.
    if temp_y0 < 0:
      rect = pymupdf.Rect(x0, y0, x1, y1)
    # In bounds, use new coordinates.
    else:
      rect = pymupdf.Rect(x0, temp_y0, x1, temp_y1)
    
    page.insert_image(rect, filename=stamp_path)

  doc.save(output_pdf)
  doc.close()


def main():
  # Add the stamp to the pdf.
  add_stamp("document2.pdf", "stamped_doc.pdf", "stamp.png")


if __name__ == "__main__":
  main()
