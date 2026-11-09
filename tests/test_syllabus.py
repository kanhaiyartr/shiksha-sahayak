from app.syllabus import list_catalog, lookup_syllabus_hint


def test_every_class_has_five_subjects_and_chapters():
    for class_level in [str(number) for number in range(1, 13)]:
        for language in ("en", "hi"):
            catalog = list_catalog(class_level, language)
            assert len(catalog["subjects"]) == 5
            assert catalog["sample"] is True
            for subject in catalog["subjects"]:
                assert subject["chapters"]
                assert all(chapter["topic"] and chapter["title"] for chapter in subject["chapters"])


def test_eval_topics_resolve_for_class_five():
    hint = lookup_syllabus_hint("5", "Mathematics", "Fractions", "en")
    assert "not-found" not in hint["locator"]
    assert "fraction" in hint["note"].casefold()
    hindi = lookup_syllabus_hint("5", "गणित", "भिन्न", "hi")
    assert "not-found" not in hindi["locator"]


def test_search_filters_subjects():
    catalog = list_catalog("5", "en", "Fraction")
    names = [subject["name"] for subject in catalog["subjects"]]
    assert names == ["Mathematics"]
    assert catalog["subjects"][0]["chapters"][0]["topic"] == "Fractions"
