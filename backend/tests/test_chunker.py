"""
Tests for Legal Structure Parser and Section-Aware Chunker
"""
from app.ingestion.legal_parser import parse_legal_structure
from app.ingestion.chunker import chunk_document


def test_legal_parser_identifies_sections():
    sample_statute = """
CHAPTER II
INVENTIONS NOT PATENTABLE

Section 3. What are not inventions.
The following are not inventions within the meaning of this Act,—
(a) an invention which is frivolous or which claims anything obvious;
(b) an invention the primary or intended use or commercial exploitation of which would be contrary to public order.

Section 4. Inventions relating to atomic energy not patentable.
No patent shall be granted in respect of an invention relating to atomic energy falling within sub-section (1) of section 20 of the Atomic Energy Act, 1962.
"""
    parsed = parse_legal_structure(sample_statute, document_type="act")
    assert len(parsed.provisions) >= 2

    sections = [p for p in parsed.provisions if p.section_no]
    assert len(sections) >= 2
    assert any(s.section_no == "3" for s in sections)
    assert any(s.section_no == "4" for s in sections)


def test_chunker_preserves_metadata():
    sample_statute = """
Section 18. Application for registration.
(1) Any person claiming to be the proprietor of a trade mark used or proposed to be used by him, who is desirous of registering it, shall apply in writing to the Registrar in the prescribed manner for the registration of his trade mark.
"""
    parsed = parse_legal_structure(sample_statute, document_type="act")
    chunks = chunk_document(
        parsed_doc=parsed,
        document_title="Trade Marks Act, 1999",
        source_url="https://ipindia.gov.in/trade-marks.htm",
        authority="IP India",
        domain="trademark",
        document_type="act",
    )

    assert len(chunks) >= 1
    assert chunks[0].section_no == "18"
    assert chunks[0].domain == "trademark"
    assert chunks[0].authority == "IP India"
    assert chunks[0].content_hash != ""
