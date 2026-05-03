import pymupdf

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
  margin = 20

  for page_num in pages_to_stamp:
    # PDF page indices start at 0
    page = doc[page_num - 1]
    
    # Obtain page dimensions.
    br = page.rect.br
    rect = pymupdf.Rect(
      # x0 = 612 - 192 - 20 = 400
      # y0 = 792 - 53 - 20 = 719
      # x1 = 612 - 20 = 592
      # y1 = 792 - 20 = 772
      br.x - stamp_width - margin,
      br.y - stamp_height - margin,
      br.x - margin,
      br.y - margin
    )
    page.insert_image(rect, filename=stamp_path)

  doc.save(output_pdf)
  doc.close()


def main():
  # Add the stamp to the pdf.
  add_stamp("document.pdf", "stamped_doc.pdf", "stamp.png")


if __name__ == "__main__":
  main()
