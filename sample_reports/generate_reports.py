"""
Generates the sample quarterly statement PDFs used by the demo.

These are synthetic documents for demoing Box AI (summary + structured
extraction) against realistic-looking wealth management statements. All
figures, names, and account numbers are fictional.

Requires: pip install reportlab
Run: python sample_reports/generate_reports.py
"""

import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

styles = getSampleStyleSheet()
TITLE_STYLE = ParagraphStyle("StatementTitle", parent=styles["Title"], fontSize=18, spaceAfter=2)
SUBTITLE_STYLE = ParagraphStyle("StatementSubtitle", parent=styles["Normal"], fontSize=10, textColor=colors.grey)
SECTION_STYLE = ParagraphStyle("Section", parent=styles["Heading2"], fontSize=12, spaceBefore=16, spaceAfter=6)
BODY_STYLE = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5, leading=13)
DISCLAIMER_STYLE = ParagraphStyle("Disclaimer", parent=styles["Normal"], fontSize=7.5, textColor=colors.grey, spaceBefore=18)

SUMMARY_TABLE_STYLE = TableStyle(
    [
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEBELOW", (0, -1), (-1, -1), 0.75, colors.black),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]
)

HOLDINGS_HEADER_STYLE = TableStyle(
    [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, colors.black),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.grey),
    ]
)


def money(value):
    value += 0.0  # normalize -0.0 to 0.0, which otherwise formats as "-0.00"
    if value < 0:
        return f"(${abs(value):,.2f})"
    return f"${value:,.2f}"


def build_statement(
    filename,
    client_name,
    account_number,
    quarter_label,
    period_label,
    beginning,
    contributions,
    withdrawals,
    net_gain,
    ending,
    holdings,
    performance_note,
):
    path = os.path.join(OUTPUT_DIR, filename)
    doc = SimpleDocTemplate(
        path,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )

    story = [
        Paragraph("Quarterly Statement", TITLE_STYLE),
        Paragraph(f"{quarter_label}&nbsp;&nbsp;&nbsp;{period_label}", SUBTITLE_STYLE),
        Spacer(1, 6),
        Paragraph(f"Prepared for: {client_name}&nbsp;&nbsp;|&nbsp;&nbsp;Account: {account_number}", BODY_STYLE),
        Paragraph("Account summary", SECTION_STYLE),
        Table(
            [
                ["Beginning value", money(beginning)],
                ["Contributions", money(contributions)],
                ["Withdrawals", money(-withdrawals)],
                ["Net market gain" if net_gain >= 0 else "Net market loss", money(net_gain)],
                ["Ending value", money(ending)],
            ],
            colWidths=[3 * inch, 2 * inch],
            style=SUMMARY_TABLE_STYLE,
        ),
        Paragraph("Holdings", SECTION_STYLE),
    ]

    holdings_rows = [["Asset", "Ticker", "Shares", "Price", "Market value"]]
    for asset, ticker, shares, price, market_value in holdings:
        holdings_rows.append(
            [
                asset,
                ticker or "-",
                f"{shares:,.2f}" if shares is not None else "-",
                f"${price:,.2f}" if price is not None else "-",
                money(market_value),
            ]
        )
    story.append(
        Table(
            holdings_rows,
            colWidths=[2.1 * inch, 0.8 * inch, 1 * inch, 0.9 * inch, 1.2 * inch],
            style=HOLDINGS_HEADER_STYLE,
        )
    )

    story.append(Paragraph("Performance notes", SECTION_STYLE))
    story.append(Paragraph(performance_note, BODY_STYLE))

    story.append(
        Paragraph(
            "This is a sample document generated for demonstration purposes only. "
            "All figures, names, and account numbers are fictional and do not represent "
            "any real account, client, or financial advice.",
            DISCLAIMER_STYLE,
        )
    )

    doc.build(story)
    print(f"Generated {path}")


def main():
    # Acme Wealth Client, Account WM-88213 — a down quarter, ahead of the
    # existing Q3 2026 statement. Exercises the "loss" / red-indicator path.
    build_statement(
        filename="q1_statement.pdf",
        client_name="Acme Wealth Client",
        account_number="WM-88213",
        quarter_label="Q1 2026",
        period_label="January 1 - March 31, 2026",
        beginning=1798650.10,
        contributions=20000.00,
        withdrawals=5000.00,
        net_gain=-42310.85,
        ending=1771339.25,
        holdings=[
            ("US Large Cap Equity Fund", "USLCX", 4050.00, 128.40, 520020.00),
            ("International Equity Fund", "INTLX", 2980.00, 55.10, 164198.00),
            ("Core Bond Fund", "CBFX", 8200.00, 97.85, 802370.00),
            ("Municipal Bond Fund", "MUBX", 2100.00, 53.90, 113190.00),
            ("Cash & equivalents", None, None, None, 171561.25),
        ],
        performance_note=(
            "Portfolio performance for the quarter was pressured by a broad equity "
            "pullback in January and February, with domestic and international holdings "
            "both declining. Fixed income holdings partially offset losses, and the "
            "portfolio recovered some ground in March as markets stabilized."
        ),
    )

    # Acme Wealth Client, Account WM-88213 — bridges the Q1 ending value to
    # the existing Q3 statement's beginning value, so the full-year story
    # (Q1 loss -> Q2 recovery -> Q3/Q4 growth) reconciles quarter to quarter.
    build_statement(
        filename="q2_statement.pdf",
        client_name="Acme Wealth Client",
        account_number="WM-88213",
        quarter_label="Q2 2026",
        period_label="April 1 - June 30, 2026",
        beginning=1771339.25,
        contributions=15000.00,
        withdrawals=8000.00,
        net_gain=63971.30,
        ending=1842310.55,
        holdings=[
            ("US Large Cap Equity Fund", "USLCX", 4130.00, 135.20, 558376.00),
            ("International Equity Fund", "INTLX", 3040.00, 58.15, 176776.00),
            ("Core Bond Fund", "CBFX", 8370.00, 98.30, 822771.00),
            ("Municipal Bond Fund", "MUBX", 2150.00, 54.10, 116315.00),
            ("Cash & equivalents", None, None, None, 168072.55),
        ],
        performance_note=(
            "Portfolio performance rebounded in the second quarter as equity markets "
            "recovered from the Q1 pullback. Domestic and international equities both "
            "posted gains, and fixed income continued to provide steady returns. The "
            "account fully recovered its year-to-date losses by the end of the quarter."
        ),
    )

    # Acme Wealth Client, Account WM-88213 — the quarter after the existing
    # Q3 2026 statement, continuing the same account's story forward.
    build_statement(
        filename="q4_statement.pdf",
        client_name="Acme Wealth Client",
        account_number="WM-88213",
        quarter_label="Q4 2026",
        period_label="October 1 - December 31, 2026",
        beginning=1925524.67,
        contributions=10000.00,
        withdrawals=15000.00,
        net_gain=54802.31,
        ending=1975326.98,
        holdings=[
            ("US Large Cap Equity Fund", "USLCX", 4320.10, 146.02, 630822.20),
            ("International Equity Fund", "INTLX", 3058.44, 60.10, 183812.65),
            ("Core Bond Fund", "CBFX", 8610.55, 99.05, 852895.03),
            ("Municipal Bond Fund", "MUBX", 2150.00, 54.75, 117712.50),
            ("Cash & equivalents", None, None, None, 190084.60),
        ],
        performance_note=(
            "Portfolio performance for the quarter was driven primarily by continued "
            "strength in domestic equities and steady fixed income returns, while "
            "international holdings remained a modest drag. The team trimmed the "
            "international allocation slightly during the quarter to reduce volatility."
        ),
    )

    # A second client — same quarter as the original statement, for
    # demoing multi-client comparisons and a different holdings mix.
    build_statement(
        filename="fairview_q3_statement.pdf",
        client_name="Fairview Family Trust",
        account_number="FT-40217",
        quarter_label="Q3 2026",
        period_label="July 1 - September 30, 2026",
        beginning=3412880.40,
        contributions=0.00,
        withdrawals=50000.00,
        net_gain=121004.65,
        ending=3483885.05,
        holdings=[
            ("Global Equity Fund", "GLEQX", 20000.00, 88.10, 1762000.00),
            ("Core Bond Fund", "CBFX", 8000.00, 98.71, 789680.00),
            ("Real Assets Fund", "REALX", 4800.00, 102.35, 491280.00),
            ("Short-Term Treasury Fund", "STTX", 3900.00, 99.10, 386490.00),
            ("Cash & equivalents", None, None, None, 54435.05),
        ],
        performance_note=(
            "Performance was led by strong global equity returns, supported by steady "
            "income from fixed income and real asset allocations. A scheduled trust "
            "distribution of $50,000 was made during the quarter per the trust agreement."
        ),
    )

    # A third client — conservative, income-focused retirement trust. No
    # new contributions, a regular distribution, and a heavy bond/dividend
    # tilt, for demoing a very different holdings mix and risk profile.
    build_statement(
        filename="whitfield_q3_statement.pdf",
        client_name="Whitfield Retirement Trust",
        account_number="WT-52104",
        quarter_label="Q3 2026",
        period_label="July 1 - September 30, 2026",
        beginning=2150780.30,
        contributions=0.00,
        withdrawals=32000.00,
        net_gain=41206.90,
        ending=2159987.20,
        holdings=[
            ("Core Bond Fund", "CBFX", 12500.00, 98.71, 1233875.00),
            ("Dividend Equity Fund", "DIVQX", 8200.00, 76.40, 626480.00),
            ("Municipal Bond Fund", "MUBX", 4300.00, 54.30, 233490.00),
            ("Cash & equivalents", None, None, None, 66142.20),
        ],
        performance_note=(
            "Performance was steady and income-driven, consistent with the trust's "
            "conservative mandate. Dividend equity holdings contributed modestly to "
            "growth while the bond allocation provided stable income to support the "
            "quarter's distribution."
        ),
    )

    # A fourth client — growth/alternatives-focused family office. A capital
    # call, a down quarter driven by private equity marks, and a holdings
    # mix (growth equity, PE, hedge strategies) unlike any other client.
    build_statement(
        filename="nakamura_q3_statement.pdf",
        client_name="Nakamura Family Office",
        account_number="NFO-30188",
        quarter_label="Q3 2026",
        period_label="July 1 - September 30, 2026",
        beginning=8420150.75,
        contributions=250000.00,
        withdrawals=0.00,
        net_gain=-186340.20,
        ending=8483810.55,
        holdings=[
            ("Growth Equity Fund", "GRWTX", 18500.00, 210.44, 3893140.00),
            ("Private Equity Fund", "PEFX", 4200.00, 612.75, 2573550.00),
            ("Hedge Strategies Fund", "HDGX", 3100.00, 342.10, 1060510.00),
            ("Core Bond Fund", "CBFX", 6800.00, 98.71, 671228.00),
            ("Cash & equivalents", None, None, None, 285382.55),
        ],
        performance_note=(
            "Portfolio performance was pressured by a pullback in growth equities and "
            "mark-to-market weakness in the private equity allocation, partially offset "
            "by hedge fund strategies that helped limit downside. A scheduled capital "
            "call of $250,000 was funded during the quarter."
        ),
    )


if __name__ == "__main__":
    main()
