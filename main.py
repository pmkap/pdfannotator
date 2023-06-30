import io
import os
from typing import Annotated, Union

from fastapi import FastAPI, Form, UploadFile
from fastapi.responses import StreamingResponse
from fpdf import FPDF
from pypdf import PdfWriter

app = FastAPI()

@app.post("/annotate/")
async def create_file(
    file: UploadFile,
    text: Annotated[str, Form()],
    token: Annotated[Union[str, None], Form()] = None,
):
    if token !=  os.environ.get('PDFANNOTATOR_TOKEN'):
        return {"error": "wrong token"}

    stream = annotate_pdf(file.file.read(), text)

    headers = {
        'Content-Disposition': f'attachment; filename={file.filename}'
    }
    return StreamingResponse(stream, headers=headers, media_type="application/pdf")

def annotate_pdf(in_bytes: bytes, text: str) -> io.BytesIO:
    pdf = PdfWriter()
    pdf.append(io.BytesIO(in_bytes))

    page = pdf.get_page(0)
    dim = [x/72*25.4 for x in page.mediabox[2:]]

    overlay = FPDF()
    overlay.add_page(format=dim)
    overlay.set_font('helvetica', size=14)
    overlay.set_text_color(255, 0, 0)
    overlay.set_margins(left=60, top=0)
    overlay.multi_cell(w=200, txt=text)

    pdf2 = PdfWriter()
    pdf2.append(io.BytesIO(overlay.output()))
    overlay_page = pdf2.get_page(0)

    page.merge_page(overlay_page)

    b = io.BytesIO()
    pdf.write(b)
    b.seek(0)

    return b
