import pytest
from pathlib import Path
from src.processor import DocumentProcessor
from src.parser import format_doc

DEFAULT_POLICIES = {
    "ads": {"pos": True, "neg": True},
    "cn": {"pos": True, "neg": True},
}


class TestDocumentProcessor:
    def test_simple_processing(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()
        
        test_file = source_dir / "test"
        test_file.write_text("google.com\nfacebook.com")
        
        content = format_doc(test_file)
        processed = {}
        
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["test"], processed
        )
        doc.process()
        
        assert len(doc.result) == 2
        assert ".google.com\n" in doc.result
        assert ".facebook.com\n" in doc.result
    
    def test_full_domain(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()
        
        test_file = source_dir / "test"
        test_file.write_text("full:analytics.google.com")
        
        content = format_doc(test_file)
        processed = {}
        
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["test"], processed
        )
        doc.process()
        
        assert "analytics.google.com\n" in doc.result
    
    def test_keyword(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()
        
        test_file = source_dir / "test"
        test_file.write_text("keyword:google")
        
        content = format_doc(test_file)
        processed = {}
        
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["test"], processed
        )
        doc.process()
        
        assert "keyword:google\n" in doc.result
    
    def test_regexp(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()
        
        test_file = source_dir / "test"
        test_file.write_text("regexp:^google.*")
        
        content = format_doc(test_file)
        processed = {}
        
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["test"], processed
        )
        doc.process()
        
        assert "regexp:^google.*\n" in doc.result
    
    def test_include(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()
        
        simple_file = source_dir / "simple"
        simple_file.write_text("google.com\nfacebook.com")
        
        main_file = source_dir / "main"
        main_file.write_text("include:simple")
        
        content = format_doc(main_file)
        processed = {}
        
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["main"], processed
        )
        doc.process()
        
        assert ".google.com\n" in doc.result
        assert ".facebook.com\n" in doc.result
    
    def test_include_with_positive_attr(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()
        
        ads_file = source_dir / "ads"
        ads_file.write_text("ad1.com @ads\nad2.com @ads\nnormal.com")
        
        main_file = source_dir / "main"
        main_file.write_text("include:ads@ads")
        
        content = format_doc(main_file)
        processed = {}
        
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["main"], processed,
            tag_policies=DEFAULT_POLICIES
        )
        doc.process()
        
        assert ".ad1.com\n" in doc.result
        assert ".ad2.com\n" in doc.result
        assert ".normal.com\n" not in doc.result
    
    def test_cycle_detection(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()
        
        a_file = source_dir / "a"
        a_file.write_text("include:b")
        
        b_file = source_dir / "b"
        b_file.write_text("include:a")
        
        content = format_doc(a_file)
        processed = {}
        
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["a"], processed
        )
        doc.process()
        
        assert doc.result == []
    
    def test_attrs_filtering(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()
        
        test_file = source_dir / "test"
        test_file.write_text("google.com@ads\nfacebook.com@cn\ntwitter.com")
        
        content = format_doc(test_file)
        processed = {}
        
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["test"], processed,
            tag_policies=DEFAULT_POLICIES
        )
        doc.process()
        
        result_file = release_dir / "test@ads.txt"
        assert result_file.exists()
        
        cn_file = release_dir / "test@cn.txt"
        assert cn_file.exists()

    def test_cached_include_with_attr(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()

        ads_file = source_dir / "ads"
        ads_file.write_text("ad1.com @ads\nad2.com @ads\nnormal.com")

        ads_content = format_doc(ads_file)
        processed = {}

        doc1 = DocumentProcessor(
            ads_content, source_dir, release_dir, ["ads"], processed,
            tag_policies=DEFAULT_POLICIES
        )
        doc1.process()
        assert "ads" in processed

        main_file = source_dir / "main"
        main_file.write_text("include:ads@ads")

        main_content = format_doc(main_file)
        doc2 = DocumentProcessor(
            main_content, source_dir, release_dir, ["main"], processed,
            tag_policies=DEFAULT_POLICIES
        )
        doc2.process()

        assert ".ad1.com\n" in doc2.result
        assert ".ad2.com\n" in doc2.result
        assert ".normal.com\n" not in doc2.result

    def test_multi_attr_entry_output(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()

        test_file = source_dir / "test"
        test_file.write_text("multi.com @ads @cn\nonly-ads.com @ads")

        content = format_doc(test_file)
        processed = {}

        doc = DocumentProcessor(
            content, source_dir, release_dir, ["test"], processed,
            tag_policies=DEFAULT_POLICIES
        )
        doc.process()

        ads_file = release_dir / "test@ads.txt"
        assert ads_file.exists()
        ads_content = ads_file.read_text()
        assert ".multi.com" in ads_content
        assert ".only-ads.com" in ads_content

        cn_file = release_dir / "test@cn.txt"
        assert cn_file.exists()
        cn_content = cn_file.read_text()
        assert ".multi.com" in cn_content

    def test_include_missing_file(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()

        main_file = source_dir / "main"
        main_file.write_text("include:nonexistent\ngoogle.com")

        content = format_doc(main_file)
        processed = {}

        doc = DocumentProcessor(
            content, source_dir, release_dir, ["main"], processed
        )
        doc.process()

        assert ".google.com\n" in doc.result

    def test_result_deterministic(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()

        test_file = source_dir / "test"
        test_file.write_text("a.com@ads\nb.com@cn\nc.com")

        content = format_doc(test_file)

        results = []
        for i in range(5):
            release_dir = tmp_path / f"release_{i}"
            release_dir.mkdir()
            processed = {}
            doc = DocumentProcessor(
                content, source_dir, release_dir, ["test"], processed,
                tag_policies=DEFAULT_POLICIES
            )
            doc.process()
            results.append(doc.result)

        for r in results[1:]:
            assert r == results[0]

    def test_neg_attr_output_file(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()

        test_file = source_dir / "test"
        test_file.write_text("google.com@-cn\nfacebook.com")

        content = format_doc(test_file)
        processed = {}
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["test"], processed, tag_policies=DEFAULT_POLICIES
        )
        doc.process()

        neg_file = release_dir / "test@!cn.txt"
        assert neg_file.exists()
        neg_content = neg_file.read_text()
        assert ".google.com" in neg_content

    def test_include_strips_child_attrs(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()

        child_file = source_dir / "child"
        child_file.write_text("ads1.com@ads\nads2.com@ads")

        main_file = source_dir / "main"
        main_file.write_text("include:child")

        content = format_doc(main_file)
        processed = {}
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["main"], processed, tag_policies=DEFAULT_POLICIES
        )
        doc.process()

        assert ".ads1.com\n" in doc.result
        assert ".ads2.com\n" in doc.result
        assert not (release_dir / "main@ads.txt").exists()

    def test_include_attr_not_in_parent_attrs(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()

        child_file = source_dir / "child"
        child_file.write_text("ads1.com@ads\nnormal.com")

        main_file = source_dir / "main"
        main_file.write_text("include:child@ads")

        content = format_doc(main_file)
        processed = {}
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["main"], processed, tag_policies=DEFAULT_POLICIES
        )
        doc.process()

        assert ".ads1.com\n" in doc.result
        assert ".normal.com\n" not in doc.result
        assert not (release_dir / "main@ads.txt").exists()

    def test_policy_both_outputs_pos_and_neg(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()

        test_file = source_dir / "test"
        test_file.write_text("a.com@cn\nb.com@-cn")

        policies = {"cn": {"pos": True, "neg": True}}
        content = format_doc(test_file)
        processed = {}
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["test"], processed, tag_policies=policies
        )
        doc.process()

        assert (release_dir / "test@cn.txt").exists()
        assert (release_dir / "test@!cn.txt").exists()

    def test_policy_pos_only(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()

        test_file = source_dir / "test"
        test_file.write_text("a.com@cn\nb.com@-cn")

        policies = {"cn": {"pos": True, "neg": False}}
        content = format_doc(test_file)
        processed = {}
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["test"], processed, tag_policies=policies
        )
        doc.process()

        assert (release_dir / "test@cn.txt").exists()
        assert not (release_dir / "test@!cn.txt").exists()

    def test_policy_neg_only(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()

        test_file = source_dir / "test"
        test_file.write_text("a.com@cn\nb.com@-cn")

        policies = {"cn": {"pos": False, "neg": True}}
        content = format_doc(test_file)
        processed = {}
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["test"], processed, tag_policies=policies
        )
        doc.process()

        assert not (release_dir / "test@cn.txt").exists()
        assert (release_dir / "test@!cn.txt").exists()

    def test_policy_off(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()

        test_file = source_dir / "test"
        test_file.write_text("a.com@cn\nb.com@-cn")

        policies = {"cn": {"pos": False, "neg": False}}
        content = format_doc(test_file)
        processed = {}
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["test"], processed, tag_policies=policies
        )
        doc.process()

        assert not (release_dir / "test@cn.txt").exists()
        assert not (release_dir / "test@!cn.txt").exists()

    def test_policy_unconfigured_tag_defaults_false(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()

        test_file = source_dir / "test"
        test_file.write_text("a.com@cn\nb.com@-cn")

        content = format_doc(test_file)
        processed = {}
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["test"], processed, tag_policies={}
        )
        doc.process()

        assert not (release_dir / "test@cn.txt").exists()
        assert not (release_dir / "test@!cn.txt").exists()

    def test_policy_missing_field_defaults_false(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()

        test_file = source_dir / "test"
        test_file.write_text("a.com@cn\nb.com@-cn")

        policies = {"cn": {"pos": True}}
        content = format_doc(test_file)
        processed = {}
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["test"], processed, tag_policies=policies
        )
        doc.process()

        assert (release_dir / "test@cn.txt").exists()
        assert not (release_dir / "test@!cn.txt").exists()

    def test_base_file_generated_for_all_tagged_entries(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()

        test_file = source_dir / "cloudflare-cn"
        test_file.write_text("a.com@cn\nb.com@cn")

        content = format_doc(test_file)
        processed = {}
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["cloudflare-cn"], processed, tag_policies=DEFAULT_POLICIES
        )
        doc.process()

        assert (release_dir / "cloudflare-cn.txt").exists()
        assert (release_dir / "cloudflare-cn@cn.txt").exists()

    def test_base_file_generated_for_all_negative_entries(self, tmp_path):
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        release_dir = tmp_path / "release"
        release_dir.mkdir()

        test_file = source_dir / "geolocation-!cn"
        test_file.write_text("a.com@-cn\nb.com@-cn")

        content = format_doc(test_file)
        processed = {}
        doc = DocumentProcessor(
            content, source_dir, release_dir, ["geolocation-!cn"], processed, tag_policies=DEFAULT_POLICIES
        )
        doc.process()

        assert (release_dir / "geolocation-!cn.txt").exists()
        assert (release_dir / "geolocation-!cn@!cn.txt").exists()
