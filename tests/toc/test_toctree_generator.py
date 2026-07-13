# =====================================================================================
#  C O P Y R I G H T
# -------------------------------------------------------------------------------------
#  Copyright (c) 2023 by Robert Bosch GmbH. All rights reserved.
#
#  Author(s):
#  - Markus Braun, :em engineering methods AG (contracted by Robert Bosch GmbH)
# =====================================================================================
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from packaging.version import Version

from doxysphinx.toc import DoxygenTocGenerator

###### Test constants ######################################################

# Doxygen versions under test. 1.8.13 uses modules.html. Around 1.9.5 and later use topics.html.
DOXYGEN_VERSIONS = ["1.8.13", "1.9.8", "1.14.0", "1.17.0"]

# Fixtures directory with test data for different doxygen versions.
FIXTURES = Path(__file__).parent / "fixtures"

###### Test helpers ########################################################

def uses_topics_html(version: str) -> bool:
    """topics.html was introduced in newer doxygen while modules.html was used in older Doxygen versions."""
    return Version(version) >= Version("1.9.5")

def expected_api_reference_docname(version: str) -> str:
    """Return the expected api reference docname for a given doxygen version."""
    return "topics" if uses_topics_html(version) else "modules"

def get_fixture_dir(version: str) -> Path:
    """Gets fixture directory for specific doxygen version '1.9.8' -> fixtures/doxygen_1_9_8"""
    return FIXTURES / f"doxygen_{version.replace('.', '_')}"

def make_test_dir(tmp_path: Path, version: str) -> Path:
    """Copy all files from the version fixture dir into tmp_path."""
    fixture_dir = get_fixture_dir(version)
    if not fixture_dir.exists():
        pytest.skip(
            f"Fixture for doxygen {version} does not exist. Please run: "
            f"DOXYGEN_VERSION={version} bash tests/toc/fixtures/generate_fixtures.sh"
        )
    for src in fixture_dir.iterdir():
        if src.is_file():
            shutil.copy(src, tmp_path / src.name)
    return tmp_path

def has_placeholder(entry) -> bool:
    """Check if any placeholder entries remain in the tree."""
    if entry.title == "__placeholder__":
        return True
    return any(has_placeholder(c) for c in entry.children)

###### Begin Tests #########################################################

class TestCommon:
    """Tests that should run for all supported doxygen versions tested in DOXYGEN_VERSIONS."""
   
    @pytest.mark.parametrize("version", DOXYGEN_VERSIONS)
    def test_toctree_format(self, tmp_path, version):
        """Generated toctree should have valid RST directive format."""
        test_dir = make_test_dir(tmp_path, version)
        tocgen = DoxygenTocGenerator(test_dir)
        result = list(tocgen.generate_toc_for(Path("index.html")))
        
        assert result[0] == ".. toctree::"
        assert result[1].startswith("   :caption:")
        assert result[2] == "   :maxdepth: 2"
        assert result[3] == "   :hidden:"
        assert result[4] == ""
        assert result[-1] == ""
        
    @pytest.mark.parametrize("version", DOXYGEN_VERSIONS)
    def test_illegal_chars_in_menu(self, tmp_path, version):
        """Menu entries with illegal filename chars should be sanitized."""
        test_dir = make_test_dir(tmp_path, version)
        tocgen = DoxygenTocGenerator(test_dir)
        # illegal__chars is top-level so appears in the api overview page toctree
        api_docname = expected_api_reference_docname(version)
        result = list(tocgen.generate_toc_for(Path(f"{api_docname}.html")))
            
        assert any("Illegal/#^ chárs" in line for line in result)
        assert any("group__illegal____chars" in line for line in result)

    @pytest.mark.parametrize("version", DOXYGEN_VERSIONS)
    def test_api_reference_detection(self, tmp_path, version):
        """Should detect topics.html (>=1.10.0) or modules.html (<1.10.0)."""
        test_dir = make_test_dir(tmp_path, version)
        tocgen = DoxygenTocGenerator(test_dir)
        
        assert tocgen._api_reference_entry is not None
        assert tocgen._api_reference_entry.docname == expected_api_reference_docname(version)

    @pytest.mark.parametrize("version", DOXYGEN_VERSIONS)
    def test_api_reference_entry_title(self, tmp_path, version):
        """API reference root should have title 'API Reference'."""
        test_dir = make_test_dir(tmp_path, version)
        tocgen = DoxygenTocGenerator(test_dir)
        
        if tocgen._api_reference_entry is not None:
            assert tocgen._api_reference_entry.title == "API Reference"

    @pytest.mark.parametrize("version", DOXYGEN_VERSIONS)
    def test_no_placeholders_in_api_reference_tree(self, tmp_path, version):
        """No placeholder entries should remain after tree construction."""
        test_dir = make_test_dir(tmp_path, version)
        tocgen = DoxygenTocGenerator(test_dir)
        
        if tocgen._api_reference_entry is not None:
            assert not has_placeholder(tocgen._api_reference_entry)

    @pytest.mark.parametrize("version", DOXYGEN_VERSIONS)
    def test_api_reference_nested_children(self, tmp_path, version):
        """Children should be nested under their parent."""
        test_dir = make_test_dir(tmp_path, version)
        tocgen = DoxygenTocGenerator(test_dir)
        
        # root has 3 top-level groups: core, extra, illegal__chars
        root = tocgen._api_reference_entry
        assert len(root.children) == 3
        
        # Check that the "core" child has 2 children: "core__io" and "core__utils"
        core = root.children[0]
        assert core.docname == "group__core"
        assert len(core.children) == 2
        assert core.children[0].docname == "group__core__io"
        assert core.children[1].docname == "group__core__utils"
        
        # Check that the "extra" child has no children (is a leaf)
        extra = root.children[1]
        assert extra.docname == "group__extra"
        assert extra.is_leaf
        
        # Check that the "illegal" group has 2 children
        illegal = root.children[2]
        assert illegal.docname == "group__illegal____chars"
        assert len(illegal.children) == 2
        assert illegal.children[0].docname == "group__illegal__child1"
        assert illegal.children[1].docname == "group__illegal__child2"
        
    @pytest.mark.parametrize("version", DOXYGEN_VERSIONS)
    def test_group_pages_get_toc(self, tmp_path, version):
        """Group pages with children should get a toctree."""
        test_dir = make_test_dir(tmp_path, version)
        tocgen = DoxygenTocGenerator(test_dir)
        result = list(tocgen.generate_toc_for(Path("group__core.html")))
        
        assert result[0] == ".. toctree::"
        assert any("group__core__io" in line for line in result)
        assert any("group__core__utils" in line for line in result)

    @pytest.mark.parametrize("version", DOXYGEN_VERSIONS)
    def test_leaf_group_produces_no_toc(self, tmp_path, version):
        """Leaf group pages should produce no toctree."""
        test_dir = make_test_dir(tmp_path, version)
        tocgen = DoxygenTocGenerator(test_dir)
        result = list(tocgen.generate_toc_for(Path("group__extra.html")))
        
        assert result == []
    
    @pytest.mark.parametrize("version", DOXYGEN_VERSIONS)
    def test_api_overview_page_gets_toc(self, tmp_path, version):
        """The topics/modules overview page itself should get a toctree."""
        test_dir = make_test_dir(tmp_path, version)
        tocgen = DoxygenTocGenerator(test_dir)
        api_page = f"{expected_api_reference_docname(version)}.html"
        result = list(tocgen.generate_toc_for(Path(api_page)))
        
        # Check that the toctree contains the top-level groups "core" and "extra"
        assert result[0] == ".. toctree::"
        assert any("group__core" in line for line in result)
        assert any("group__extra" in line for line in result)
        
    @pytest.mark.parametrize("version", DOXYGEN_VERSIONS)
    def test_correct_api_reference_file_in_fixture(self, version):
        """Fixture should contain the correct api reference file for the version."""
        fixture = get_fixture_dir(version)
       
        if not fixture.exists():
            pytest.fail(f"Fixture for doxygen {version} not generated yet")
        
        # Check that the expected file exists and the other does not
        if uses_topics_html(version):
            assert (fixture / "topics.html").exists(), f"Expected topics.html in {fixture}"
            assert not (fixture / "modules.html").exists(), f"Unexpected modules.html in {fixture}"
        else:
            assert (fixture / "modules.html").exists(), f"Expected modules.html in {fixture}"
            assert not (fixture / "topics.html").exists(), f"Unexpected topics.html in {fixture}"
