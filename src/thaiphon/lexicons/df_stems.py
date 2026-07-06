"""Sanskrit/Pali stems whose final consonant re-sounds in compounds.

In learned compounds the stem-final consonant is double-functioning: it
closes the stem syllable AND re-sounds as the onset of a linking
syllable with inherent /a/ — วิทยา = วิด + ทะ + ยา, ราชการ = ราด + ชะ +
กาน, ตุ๊กตา = ตุ๊ก + กะ + ตา. The pattern is morphological, not
orthographic: the same written shape stays a plain coda in native
compounds (ลูกค้า = ลูก + ค้า), so it cannot be derived from spelling
alone. This module lists the productive stems — each entry attested
across multiple dictionary compounds with the re-sounding reading, and
checked against words that share the written shape without it.

An entry is matched against the exact concatenation of the syllable
token preceding the pivot consonant and the pivot itself (tone marks
included), so a stem fires in any compound position (ราชการ, เยาวราช,
มหาวิทยาลัย) without capturing look-alike native syllables (กระตุก
does not match ตุ๊ก).
"""

from __future__ import annotations

#: Stem strings (last syllable + double-functioning final consonant).
DF_STEMS: frozenset[str] = frozenset(
    {
        "วิท",              # วิทยา, วิทยุ, มหาวิทยาลัย
        "ราช",              # ราชการ, ราชวงศ์
        "เอก",              # เอกชน, เอกภาพ
        "อุป",              # อุปนิสัย, อุปกรณ์
        "รัฐ",        # รัฐบาล, รัฐศาสตร์
        "ทัศ",              # ทัศนะ, ทัศนคติ
        "เจต",              # เจตนา
        "ศุภ",              # ศุภนิมิต
        "โฆษ",              # โฆษณา
        "พัฒ",        # พัฒนา
        "เวช",              # เวชศาสตร์
        "พิธ",              # พิพิธภัณฑ์
        "ตุ๊ก",             # ตุ๊กตา
        "พัท",        # พัทยา
        "สัต",        # สัตวาร
        "เวท",              # เวทนา
        "อัศ",        # อัศวิน
        "ลัค",        # ลัคนา
        "เยาว",             # เยาวราช (via เยา + ว pivot)
        "ลิข",              # ลิขสิทธิ์
        "ศุล",              # ศุลกากร
        "พัส",        # พัสดุ
        "จัต",        # จัตวา
        "บุพ",              # บุพการี
        "อัษ",        # อัษฎางค์
        "หิม",              # หิมพานต์
        "จุล",              # จุลชีพ
        "ภาว",              # ภาวนา
        "ราศ",              # ราศี compounds
        "ไสย",              # ไสยศาสตร์
        "ราพ",              # ราพณาสูร
        "บุษ",              # บุษบง
        "เจร",              # เจรจา
        "พิส",              # พิสดาร
        # Word-initial bare pairs whose second consonant re-sounds
        # (มลทิน = mohn-la-thin). Most pair stems vary per compound
        # (ผลไม้ re-sounds, ผลงาน does not) and stay out of this list.
        "มล",               # มลทิน, มลพิษ
        "ทศ",               # ทศนิยม
        "นพ",               # นพเคราะห์
        "ยม",               # ยมโลก
        "ปฐ",               # ปฐพี
    }
)


def is_df_stem(stem: str) -> bool:
    """True when ``stem`` (tone-stripped syllable + pivot consonant)
    re-sounds its final consonant as a linking syllable."""
    return stem in DF_STEMS


__all__ = ["DF_STEMS", "is_df_stem"]
