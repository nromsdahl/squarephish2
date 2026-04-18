from io import BytesIO

import qrcode


def generate_qr_code(data: str, size: int = 256) -> bytes:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=size // 21,  # approximate: 21 modules is QR v1
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_qr_code_ascii(data: str) -> str:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    bits = qr.modules
    inverse_color = False

    buf = ['<pre style="line-height:1">']
    for y in range(0, len(bits) - 1, 2):
        for x in range(len(bits[y])):
            if bits[y][x] == bits[y + 1][x]:
                if bits[y][x] != inverse_color:
                    buf.append("\u2588")  # █
                else:
                    buf.append(" ")
            else:
                if bits[y][x] != inverse_color:
                    buf.append("\u2580")  # ▀
                else:
                    buf.append("\u2584")  # ▄
        buf.append("\n")
    buf.append("</pre>")

    return "".join(buf)
