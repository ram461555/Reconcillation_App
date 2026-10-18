"""Generates synthetic ledger_aug2026.pdf and bank_statement_aug2026.pdf test fixtures.

The data below is transcribed verbatim from Docs' "Deshpande Print Solutions" bank
book and "Girnar Co-operative Bank" statement of account (the sample source PDFs
described in the requirement docs), so the golden CSV fixture (expected_results_aug2026.csv)
can be validated end-to-end through the real PDF-extraction pipeline.

Run: python -m tests.fixtures.generate_sample_pdfs
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

FIXTURES_DIR = Path(__file__).parent

LEDGER_HEADER = ["Date", "Voucher No.", "Particulars", "Amount (INR)"]
LEDGER_ROWS = [
    ["01/08/2026", "PAY-0801", "Rent - Shah Properties - Aug 2026", "25,000.00"],
    ["03/08/2026", "RCT-0801", "Receipt - Kalpana Events - Inv 0227", "18,500.00"],
    ["03/08/2026", "PAY-0802", "Meera Paper Mart - Bill 1187", "42,300.00"],
    ["04/08/2026", "PAY-0803", "Electricity bill - Adani - Jul 2026", "6,842.00"],
    ["04/08/2026", "PAY-0804", "Internet - Jio Fiber - Aug 2026", "1,179.00"],
    ["05/08/2026", "RCT-0802", "Receipt - Bright Minds Academy - Inv 0229", "32,000.00"],
    ["06/08/2026", "PAY-0805", "Ganesh Inks - Toner CMYK set", "15,240.00"],
    ["07/08/2026", "PAY-0806", "Salary - Sunil Pawar - Jul 2026", "22,000.00"],
    ["07/08/2026", "PAY-0807", "Salary - Priya Naik - Jul 2026", "19,500.00"],
    ["07/08/2026", "PAY-0808", "Salary - Arjun Mhatre - Jul 2026", "16,000.00"],
    ["08/08/2026", "PAY-0809", "Courier - DTDC - client dispatch", "1,240.00"],
    ["10/08/2026", "PAY-0810", "Sundry expenses", "2,360.00"],
    ["11/08/2026", "RCT-0803", "Receipt - Nirvana Wellness Spa - Inv 0230", "12,500.00"],
    ["12/08/2026", "PAY-0811", "Advance - Meera Paper Mart", "5,000.00"],
    ["12/08/2026", "PAY-0812", "Advance - Ganesh Inks", "5,000.00"],
    ["13/08/2026", "PAY-0813", "Machine AMC - Sai Copier Services - Q2", "9,000.00"],
    ["14/08/2026", "RCT-0804", "Receipt - Kalpana Events - Inv 0231", "27,600.00"],
    ["14/08/2026", "PAY-0814", "Packaging - Om Sai Packers", "4,900.00"],
    ["17/08/2026", "PAY-0815", "Fuel - delivery van", "3,200.00"],
    ["18/08/2026", "PAY-0816", "GST payment - Jul 2026", "21,870.00"],
    ["19/08/2026", "RCT-0805", "Receipt - Bright Minds Academy - Inv 0233", "1,25,000.00"],
    ["20/08/2026", "PAY-0817", "Meera Paper Mart - Bill 1203", "38,750.00"],
    ["20/08/2026", "PAY-0817", "Meera Paper Mart - Bill 1203", "38,750.00"],
    ["21/08/2026", "PAY-0818", "Loan EMI - Girnar Bank - Aug 2026", "11,430.00"],
    ["22/08/2026", "RCT-0806", "Receipt - Nirvana Wellness Spa - Chq 118834", "9,800.00"],
    ["24/08/2026", "PAY-0819", "Petty cash withdrawal", "5,000.00"],
    ["25/08/2026", "PAY-0820", "Stationery - Kamal Stores", "1,875.00"],
    ["26/08/2026", "RCT-0807", "Receipt - Prime Realty - Inv 0235", "45,000.00"],
    ["27/08/2026", "PAY-0821", "Ganesh Inks - Bill 4470", "8,320.00"],
    ["28/08/2026", "PAY-0822", "Sai Copier Services - Spare parts", "6,600.00"],
    ["29/08/2026", "PAY-0823", "Salary advance - Arjun Mhatre", "5,000.00"],
    ["31/08/2026", "PAY-0824", "Website hosting - Hostinger - annual", "3,588.00"],
]

BANK_HEADER = ["Txn Date", "Ref No.", "Description", "Amount (INR)", "Dr/Cr", "Balance (INR)"]
BANK_ROWS = [
    ["03-Aug-2026", "N215261034512", "NEFT SHAH PROPERTIES RENT AUG 2026", "25,000.00", "Dr", "1,59,320.55"],
    ["03-Aug-2026", "N215261098877", "NEFT CR KALPANA EVENTS INV 0227", "18,450.00", "Cr", "1,77,770.55"],
    ["04-Aug-2026", "BP260804011", "BILLPAY ADANI ELECTRICITY JUL 2026", "6,842.00", "Dr", "1,70,928.55"],
    ["04-Aug-2026", "BP260804012", "BILLPAY JIO FIBER INTERNET AUG 2026", "1,179.00", "Dr", "1,69,749.55"],
    ["04-Aug-2026", "CHG2608040001", "SMS ALERT CHARGES JUL 2026", "17.70", "Dr", "1,69,731.85"],
    ["05-Aug-2026", "I522170455621", "IMPS CR BRIGHT MINDS ACADEMY INV 0229", "32,000.00", "Cr", "2,01,731.85"],
    ["06-Aug-2026", "CLG000214", "CLG CHQ 000214 MEERA PAPER MART BILL 1187", "42,300.00", "Dr", "1,59,431.85"],
    ["06-Aug-2026", "N215263344101", "NEFT GANESH INKS TONER CMYK SET", "12,540.00", "Dr", "1,46,891.85"],
    ["07-Aug-2026", "N215264400231", "NEFT SALARY SUNIL PAWAR JUL 2026", "22,000.00", "Dr", "1,24,891.85"],
    ["07-Aug-2026", "N215264400232", "NEFT SALARY PRIYA NAIK JUL 2026", "19,500.00", "Dr", "1,05,391.85"],
    ["07-Aug-2026", "N215264400233", "NEFT SALARY ARJUN MHATRE JUL 2026", "16,000.00", "Dr", "89,391.85"],
    ["08-Aug-2026", "U522010887761", "UPI DTDC COURIER CLIENT DISPATCH", "1,240.00", "Dr", "88,151.85"],
    ["10-Aug-2026", "U522211043920", "UPI AMAZON PAY ORDER 4471", "2,360.00", "Dr", "85,791.85"],
    ["12-Aug-2026", "N215272200418", "NEFT GANESH INKS ADVANCE", "5,000.00", "Dr", "80,791.85"],
    ["12-Aug-2026", "N215272200419", "NEFT MEERA PAPER MART ADVANCE", "5,000.00", "Dr", "75,791.85"],
    ["13-Aug-2026", "N215273301177", "NEFT SAI COPIER SERVICES AMC Q2", "9,000.00", "Dr", "66,791.85"],
    ["14-Aug-2026", "N215274102290", "NEFT CR KALPANA EVENTS INV 0231", "27,600.00", "Cr", "94,391.85"],
    ["14-Aug-2026", "U522610334902", "UPI OM SAI PACKERS PACKAGING", "4,810.00", "Dr", "89,581.85"],
    ["17-Aug-2026", "U522910778345", "UPI HP PETROL PUMP FUEL DELIVERY VAN", "3,200.00", "Dr", "86,381.85"],
    ["17-Aug-2026", "N215292004561", "NEFT CR NIRVANA WELLNESS SPA INV 0230", "12,500.00", "Cr", "98,881.85"],
    ["18-Aug-2026", "GST26081812340", "GST PAYMENT JUL 2026 CPIN 26081812340", "21,870.00", "Dr", "77,011.85"],
    ["18-Aug-2026", "N215302118845", "NEFT CR RUSHABH TRADERS", "7,500.00", "Cr", "84,511.85"],
    ["19-Aug-2026", "N215310923318", "NEFT CR BRIGHT MINDS ACADEMY INV 0233", "1,24,400.00", "Cr", "2,08,911.85"],
    ["20-Aug-2026", "N215320456780", "NEFT MEERA PAPER MART BILL 1203", "38,750.00", "Dr", "1,70,161.85"],
    ["21-Aug-2026", "ACH2608210099", "ACH DR GIRNAR BANK TERM LOAN EMI AUG 2026", "11,430.00", "Dr", "1,58,731.85"],
    ["24-Aug-2026", "CLG118834", "CLG CR NIRVANA WELLNESS SPA CHQ 118834", "9,800.00", "Cr", "1,68,531.85"],
    ["24-Aug-2026", "ATM5566021", "ATM CASH WDL DADAR WEST", "5,000.00", "Dr", "1,63,531.85"],
    ["25-Aug-2026", "U523710556612", "UPI KAMAL STORES STATIONERY", "1,875.00", "Dr", "1,61,656.85"],
    ["27-Aug-2026", "N215390877012", "NEFT GANESH INKS BILL 4470", "8,320.00", "Dr", "1,53,336.85"],
    ["29-Aug-2026", "I524110230987", "IMPS ARJUN MHATRE SALARY ADVANCE", "5,000.00", "Dr", "1,48,336.85"],
    ["31-Aug-2026", "POS260831118", "CARD HOSTINGER WEBSITE HOSTING ANNUAL", "3,588.00", "Dr", "1,44,748.85"],
    ["31-Aug-2026", "CHG2608310002", "MONTHLY MAINT CHARGES AUG 2026", "295.00", "Dr", "1,44,453.85"],
]


def _build_pdf(path: Path, title: str, header: list[str], rows: list[list[str]], col_widths: list[float], page_size) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=page_size, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=15 * mm, bottomMargin=15 * mm)
    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Title"]), Spacer(1, 8)]
    data = [header] + rows
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.75, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dddddd")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)


def main() -> None:
    _build_pdf(
        FIXTURES_DIR / "ledger_aug2026.pdf",
        "Deshpande Print Solutions - Bank Book - August 2026",
        LEDGER_HEADER,
        LEDGER_ROWS,
        col_widths=[26 * mm, 22 * mm, 90 * mm, 25 * mm],
        page_size=A4,
    )
    _build_pdf(
        FIXTURES_DIR / "bank_statement_aug2026.pdf",
        "Girnar Co-operative Bank - Statement of Account - August 2026",
        BANK_HEADER,
        BANK_ROWS,
        col_widths=[24 * mm, 30 * mm, 100 * mm, 24 * mm, 12 * mm, 24 * mm],
        page_size=landscape(A4),
    )
    print("Generated:", FIXTURES_DIR / "ledger_aug2026.pdf")
    print("Generated:", FIXTURES_DIR / "bank_statement_aug2026.pdf")


if __name__ == "__main__":
    main()
