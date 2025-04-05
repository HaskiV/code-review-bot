"""
Конфигурация инструментов статического анализа.
"""

# Конфигурация Pylint
PYLINT_CONFIG = {
    "disable": [
        "missing-docstring",
        "invalid-name",
        "too-many-arguments",
        "too-many-instance-attributes",
        "too-few-public-methods",
        "too-many-locals",
        "too-many-statements",
        "too-many-branches",
        "too-many-return-statements",
        "too-many-public-methods",
        "too-many-lines",
        "locally-disabled",
        "fixme",
        "suppressed-message",
        "useless-suppression",
        "deprecated-pragma",
        "use-symbolic-message-instead",
        "no-member",
        "no-name-in-module",
        "import-error"
    ],
    "max-line-length": 100,
    "good-names": ["i", "j", "k", "ex", "Run", "_", "id", "db"]
}

# Конфигурация Flake8
FLAKE8_CONFIG = {
    "max-line-length": 100,
    "ignore": ["E203", "W503", "E501"],
    "exclude": [".git", "__pycache__", "build", "dist"]
}

# Конфигурация ESLint
ESLINT_CONFIG = {
    "extends": ["eslint:recommended", "plugin:react/recommended"],
    "rules": {
        "no-console": "warn",
        "no-unused-vars": "warn",
        "react/prop-types": "off"
    }
}

# Конфигурация TSLint
TSLINT_CONFIG = {
    "extends": ["tslint:recommended"],
    "rules": {
        "no-console": false,
        "member-ordering": false,
        "object-literal-sort-keys": false
    }
}

# Конфигурация Java Checkstyle
CHECKSTYLE_CONFIG = {
    "max_line_length": 100,
    "indentation": 4,
    "braces_style": "same_line"
}

# Конфигурация C++ Cppcheck
CPPCHECK_CONFIG = {
    "enable": ["all"],
    "suppress": ["missingIncludeSystem"],
    "inline_suppression": True
}

# Конфигурация C# Roslyn
ROSLYN_CONFIG = {
    "analyzer_packages": ["Microsoft.CodeAnalysis.CSharp"],
    "rules": {
        "CA1822": "warning",  # Пометить члены как статические
        "CA2007": "warning",  # Не ожидать Task напрямую
        "CA1054": "warning"   # URI параметры не должны быть строками
    }
}

# Шаблоны команд статического анализатора
STATIC_ANALYZER_COMMANDS = {
    "pylint": "pylint --output-format=json {options} {file_path}",
    "flake8": "flake8 --format=json {options} {file_path}",
    "eslint": "eslint --format=json {options} {file_path}",
    "tslint": "tslint --format=json {options} {file_path}",
    "checkstyle": "java -jar {checkstyle_jar} -c {config_file} {file_path}",
    "cppcheck": "cppcheck --enable=all --template='{file}:{line}:{severity}:{message}' {file_path}",
    "roslyn": "dotnet {roslyn_analyzer} {file_path}"
}