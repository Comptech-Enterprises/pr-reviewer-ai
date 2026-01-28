"""
Tests for code analyzers.
"""
import pytest
from src.analyzers import (
    SecurityAnalyzer,
    QualityAnalyzer,
    PerformanceAnalyzer,
    TestingAnalyzer,
    Severity
)


class TestSecurityAnalyzer:
    """Test cases for SecurityAnalyzer."""

    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = SecurityAnalyzer({'enabled': True})
        assert analyzer.enabled is True
        assert analyzer.get_name() == "Security"

    def test_get_analysis_prompt(self):
        """Test analysis prompt generation."""
        analyzer = SecurityAnalyzer()
        prompt = analyzer.get_analysis_prompt()

        assert "SQL Injection" in prompt
        assert "XSS" in prompt
        assert "security" in prompt.lower()

    def test_get_security_patterns_python(self):
        """Test security patterns for Python."""
        analyzer = SecurityAnalyzer()
        patterns = analyzer.get_security_patterns('python')

        # Should have common and Python-specific patterns
        assert len(patterns) > 0

        # Check for hardcoded credentials pattern
        has_credentials_check = any(
            'credential' in p['name'].lower() for p in patterns
        )
        assert has_credentials_check

    def test_get_security_patterns_javascript(self):
        """Test security patterns for JavaScript."""
        analyzer = SecurityAnalyzer()
        patterns = analyzer.get_security_patterns('javascript')

        # Should include XSS patterns
        has_xss = any('xss' in p['name'].lower() for p in patterns)
        assert has_xss

    def test_disabled_analyzer(self):
        """Test disabled analyzer returns empty results."""
        analyzer = SecurityAnalyzer({'enabled': False})
        results = analyzer.analyze("code", "test.py")
        assert results == []


class TestQualityAnalyzer:
    """Test cases for QualityAnalyzer."""

    def test_initialization(self):
        """Test analyzer initialization."""
        config = {
            'enabled': True,
            'max_complexity': 15,
            'max_function_length': 100
        }
        analyzer = QualityAnalyzer(config)

        assert analyzer.enabled is True
        assert analyzer.get_complexity_threshold() == 15
        assert analyzer.get_function_length_threshold() == 100

    def test_get_analysis_prompt(self):
        """Test analysis prompt generation."""
        analyzer = QualityAnalyzer()
        prompt = analyzer.get_analysis_prompt()

        assert "code smell" in prompt.lower()
        assert "SOLID" in prompt
        assert "complexity" in prompt.lower()

    def test_default_thresholds(self):
        """Test default threshold values."""
        analyzer = QualityAnalyzer()

        assert analyzer.get_complexity_threshold() == 10
        assert analyzer.get_function_length_threshold() == 50
        assert analyzer.get_class_length_threshold() == 300


class TestPerformanceAnalyzer:
    """Test cases for PerformanceAnalyzer."""

    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = PerformanceAnalyzer()
        assert analyzer.get_name() == "Performance"

    def test_get_analysis_prompt(self):
        """Test analysis prompt generation."""
        analyzer = PerformanceAnalyzer()
        prompt = analyzer.get_analysis_prompt()

        assert "performance" in prompt.lower()
        assert "O(n" in prompt
        assert "memory" in prompt.lower()

    def test_get_performance_patterns_python(self):
        """Test performance patterns for Python."""
        analyzer = PerformanceAnalyzer()
        patterns = analyzer.get_performance_patterns('python')

        assert len(patterns) > 0

    def test_get_performance_patterns_javascript(self):
        """Test performance patterns for JavaScript."""
        analyzer = PerformanceAnalyzer()
        patterns = analyzer.get_performance_patterns('javascript')

        # Should include async patterns
        assert len(patterns) > 0


class TestTestingAnalyzer:
    """Test cases for TestingAnalyzer."""

    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = TestingAnalyzer()
        assert analyzer.get_name() == "Testing"

    def test_get_analysis_prompt(self):
        """Test analysis prompt generation."""
        analyzer = TestingAnalyzer()
        prompt = analyzer.get_analysis_prompt()

        assert "test" in prompt.lower()
        assert "edge case" in prompt.lower()
        assert "coverage" in prompt.lower()

    def test_is_test_file(self):
        """Test test file detection."""
        analyzer = TestingAnalyzer()

        assert analyzer.is_test_file("test_module.py") is True
        assert analyzer.is_test_file("module_test.py") is True
        assert analyzer.is_test_file("tests/test_file.py") is True
        assert analyzer.is_test_file("module.spec.js") is True
        assert analyzer.is_test_file("src/module.py") is False

    def test_get_test_frameworks(self):
        """Test test framework detection."""
        analyzer = TestingAnalyzer()

        python_frameworks = analyzer.get_test_frameworks('python')
        assert 'pytest' in python_frameworks
        assert 'unittest' in python_frameworks

        js_frameworks = analyzer.get_test_frameworks('javascript')
        assert 'jest' in js_frameworks

        unknown_frameworks = analyzer.get_test_frameworks('unknown')
        assert unknown_frameworks == []


class TestBaseAnalyzer:
    """Test cases for base analyzer functionality."""

    def test_severity_filtering(self):
        """Test filtering results by severity."""
        from src.analyzers.base import AnalysisResult

        analyzer = SecurityAnalyzer()

        results = [
            AnalysisResult(
                severity=Severity.CRITICAL,
                category="Security",
                title="Critical issue",
                description="Test",
                filename="test.py"
            ),
            AnalysisResult(
                severity=Severity.LOW,
                category="Security",
                title="Low issue",
                description="Test",
                filename="test.py"
            ),
            AnalysisResult(
                severity=Severity.HIGH,
                category="Security",
                title="High issue",
                description="Test",
                filename="test.py"
            )
        ]

        # Filter for HIGH and above
        filtered = analyzer.filter_by_severity(results, Severity.HIGH)

        assert len(filtered) == 2  # CRITICAL and HIGH
        assert all(r.severity in [Severity.CRITICAL, Severity.HIGH] for r in filtered)

    def test_get_language_from_filename(self):
        """Test language detection from filename."""
        analyzer = SecurityAnalyzer()

        assert analyzer.get_language_from_filename("test.py") == "python"
        assert analyzer.get_language_from_filename("test.js") == "javascript"
        assert analyzer.get_language_from_filename("test.ts") == "typescript"
        assert analyzer.get_language_from_filename("test.go") == "go"
        assert analyzer.get_language_from_filename("test.unknown") is None
