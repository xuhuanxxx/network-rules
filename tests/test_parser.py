import pytest
from pathlib import Path
from src.parser import format_doc, format_line, Entry, entry_to_domain, parse_attrs


class TestFormatDoc:
    def test_simple_content(self, tmp_path):
        test_file = tmp_path / "test"
        test_file.write_text("domain:test.com\ndomain:test2.com")
        
        result = format_doc(test_file)
        assert len(result) == 2
        assert result[0] == "domain:test.com"
        assert result[1] == "domain:test2.com"
    
    def test_comment_removal(self, tmp_path):
        test_file = tmp_path / "test"
        test_file.write_text("domain:test.com # this is comment")
        
        result = format_doc(test_file)
        assert result[0] == "domain:test.com"
    
    def test_space_handling(self, tmp_path):
        test_file = tmp_path / "test"
        test_file.write_text("include:test @ads\ninclude:test2@cn")
        
        result = format_doc(test_file)
        assert "include:test@ads" in result
        assert "include:test2@cn" in result
    
    def test_empty_lines_removed(self, tmp_path):
        test_file = tmp_path / "test"
        test_file.write_text("domain:test.com\n\n\ndomain:test2.com")
        
        result = format_doc(test_file)
        assert len(result) == 2

    def test_regexp_with_hash(self, tmp_path):
        test_file = tmp_path / "test"
        test_file.write_text("regexp:^[a-f0-9#]{32}$")
        
        result = format_doc(test_file)
        assert len(result) == 1
        assert result[0] == "regexp:^[a-f0-9#]{32}$"

    def test_regexp_with_comment(self, tmp_path):
        test_file = tmp_path / "test"
        test_file.write_text("regexp:^foo#bar$ # this is comment")
        
        result = format_doc(test_file)
        assert len(result) == 1
        assert result[0] == "regexp:^foo#bar$"


class TestFormatLine:
    def test_simple_domain(self):
        type_prefix, value, pos_attrs, neg_attrs = format_line("google.com")
        assert type_prefix == "domain"
        assert value == "google.com"
        assert pos_attrs == set()
        assert neg_attrs == set()
    
    def test_domain_with_prefix(self):
        type_prefix, value, pos_attrs, neg_attrs = format_line("domain:google.com")
        assert type_prefix == "domain"
        assert value == "google.com"
    
    def test_full_domain(self):
        type_prefix, value, pos_attrs, neg_attrs = format_line("full:analytics.google.com")
        assert type_prefix == "full"
        assert value == "analytics.google.com"
    
    def test_keyword(self):
        type_prefix, value, pos_attrs, neg_attrs = format_line("keyword:google")
        assert type_prefix == "keyword"
        assert value == "google"
    
    def test_regexp(self):
        type_prefix, value, pos_attrs, neg_attrs = format_line("regexp:^google.*")
        assert type_prefix == "regexp"
        assert value == "^google.*"
    
    def test_with_positive_attr(self):
        type_prefix, value, pos_attrs, neg_attrs = format_line("google.com@ads")
        assert type_prefix == "domain"
        assert value == "google.com"
        assert "@ads" in pos_attrs
    
    def test_with_multiple_attrs(self):
        type_prefix, value, pos_attrs, neg_attrs = format_line("google.com@ads@cn")
        assert "@ads" in pos_attrs
        assert "@cn" in pos_attrs
    
    def test_with_negative_attr(self):
        type_prefix, value, pos_attrs, neg_attrs = format_line("google.com@-cn")
        assert type_prefix == "domain"
        assert value == "google.com"
        assert "@!cn" in neg_attrs
    
    def test_include_with_attrs(self):
        type_prefix, value, pos_attrs, neg_attrs = format_line("include:category-ads@ads")
        assert type_prefix == "include"
        assert value == "category-ads"
        assert "@ads" in pos_attrs
    
    def test_include_with_negative_attr(self):
        type_prefix, value, pos_attrs, neg_attrs = format_line("include:test@-cn")
        assert type_prefix == "include"
        assert value == "test"
        assert "@!cn" in neg_attrs
    
    def test_include_with_space(self):
        type_prefix, value, pos_attrs, neg_attrs = format_line("include:test@ads")
        assert type_prefix == "include"
        assert value == "test"
        assert "@ads" in pos_attrs

    def test_regexp_with_at_sign(self):
        type_prefix, value, pos_attrs, neg_attrs = format_line("regexp:^user@domain\\.com$")
        assert type_prefix == "regexp"
        assert value == "^user@domain\\.com$"
        assert pos_attrs == set()
        assert neg_attrs == set()


class TestParseAttrs:
    def test_empty(self):
        pos, neg = parse_attrs("")
        assert pos == set()
        assert neg == set()
    
    def test_single_positive(self):
        pos, neg = parse_attrs("ads")
        assert pos == {"@ads"}
        assert neg == set()
    
    def test_single_negative(self):
        pos, neg = parse_attrs("-cn")
        assert pos == set()
        assert neg == {"@!cn"}
    
    def test_mixed(self):
        pos, neg = parse_attrs("ads-cn")
        assert "@ads-cn" in pos

    def test_bang_negative_attr(self):
        pos, neg = parse_attrs("!cn")
        assert pos == set()
        assert neg == {"@!cn"}

    def test_mixed_positive_and_negative(self):
        pos, neg = parse_attrs("ads@-cn")
        assert pos == {"@ads"}
        assert neg == {"@!cn"}

    def test_neg_attr_normalize(self):
        _, neg1 = parse_attrs("-cn")
        _, neg2 = parse_attrs("!cn")
        assert neg1 == neg2
        assert neg1 == {"@!cn"}


class TestEntryToDomain:
    def test_full(self):
        entry = Entry(type="full", value="test.com", attr=set())
        assert entry_to_domain(entry) == "test.com\n"
    
    def test_domain(self):
        entry = Entry(type="domain", value="test.com", attr=set())
        assert entry_to_domain(entry) == ".test.com\n"
    
    def test_keyword(self):
        entry = Entry(type="keyword", value="test", attr=set())
        assert entry_to_domain(entry) == "keyword:test\n"
    
    def test_regexp(self):
        entry = Entry(type="regexp", value="^test.*", attr=set())
        assert entry_to_domain(entry) == "regexp:^test.*\n"
