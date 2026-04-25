"""
Confidence Scoring Module for Vulnerability Findings

Calculates confidence scores for findings based on detection methods,
detection consistency, and vulnerability type, enabling more accurate
risk assessment and false positive reduction.
"""

from typing import List, Dict, Tuple, Optional
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence level categories"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    SUSPICIOUS = "Suspicious"


class ConfidenceScorer:
    """Calculates and manages confidence scores for vulnerability findings"""
    
    # Baseline confidence scores by vulnerability type and detection method combination
    BASELINE_CONFIDENCE = {
        "SQL Injection": {
            "error_based": 85,
            "time_based": 65,
            "error_time_combined": 90,
            "union_based": 95,
            "boolean_based": 70,
        },
        "Cross-Site Scripting": {
            "marker_reflected": 75,
            "markup_found": 80,
            "marker_markup_combined": 85,
            "dom_based": 80,
            "stored": 90,
        },
        "CSRF": {
            "token_missing": 60,
            "token_static": 75,
            "state_change_success": 85,
            "token_state_combined": 90,
        },
        "SSRF": {
            "response_contains_internal": 85,
            "timing_detected": 65,
            "error_message": 70,
            "combined": 90,
        },
        "Authentication": {
            "weak_password_policy": 70,
            "default_credentials": 85,
            "missing_mfa": 75,
            "session_fixation": 80,
            "combined": 85,
        },
        "Authorization": {
            "direct_access": 80,
            "response_timing": 65,
            "error_message": 70,
            "combined": 85,
        },
        "Insecure Direct Object Reference": {
            "direct_access": 85,
            "response_timing_similar": 70,
            "combined": 90,
        },
        "Sensitive Data Exposure": {
            "pattern_match": 70,
            "multiple_types": 80,
            "in_response_body": 85,
            "combined": 90,
        },
        "Path Traversal": {
            "file_accessed": 85,
            "error_message": 70,
            "timing_detected": 60,
            "combined": 90,
        },
        "File Upload": {
            "malicious_file_stored": 90,
            "executed": 95,
            "bypass_detected": 80,
            "filter_weakness": 75,
        },
        "Rate Limiting": {
            "threshold_exceeded": 70,
            "no_rate_limit_header": 65,
            "combined": 75,
        },
        "Business Logic": {
            "state_inconsistency": 65,
            "unauthorized_state": 75,
            "combined": 80,
        },
        "Weak Cryptography": {
            "weak_algorithm": 80,
            "short_key": 75,
            "combined": 85,
        },
        "Security Misconfiguration": {
            "default_value": 75,
            "debug_enabled": 80,
            "combined": 85,
        },
        "Injection": {
            "error_detected": 65,
            "multiple_payloads": 75,
            "combined": 80,
        },
    }
    
    # Minimum detection methods required for different confidence levels
    MIN_METHODS = {
        "High": 2,  # Multiple independent detection methods
        "Medium": 1,  # Single solid detection method
        "Low": 1,    # Single weak detection method
        "Suspicious": 1,  # Uncertain detection
    }
    
    @staticmethod
    def calculate_confidence(
        finding_type: str,
        detection_methods: List[str],
        detection_results: Dict[str, any],
        additional_factors: Optional[Dict[str, any]] = None,
    ) -> Tuple[int, str]:
        """
        Calculate confidence score (0-100) and confidence level.
        
        Args:
            finding_type: Type of vulnerability found
            detection_methods: List of detection methods used (e.g., ["error_based", "timing"])
            detection_results: Dictionary with results from each detection method
            additional_factors: Optional dict with additional scoring factors
            
        Returns:
            Tuple of (confidence_score: int, confidence_level: str)
        """
        if not detection_methods:
            return (0, ConfidenceLevel.SUSPICIOUS.value)
        
        # Get baseline confidence for this finding type
        base_confidence = ConfidenceScorer._get_baseline_confidence(
            finding_type, detection_methods
        )
        
        # Apply multipliers based on consistency
        consistency_multiplier = ConfidenceScorer._calculate_consistency_multiplier(
            detection_results
        )
        
        # Apply additional factors if provided
        factor_adjustment = ConfidenceScorer._calculate_factor_adjustment(
            additional_factors or {}
        )
        
        # Calculate final confidence
        final_confidence = int(base_confidence * consistency_multiplier + factor_adjustment)
        final_confidence = max(0, min(100, final_confidence))  # Clamp to 0-100
        
        # Determine confidence level
        if final_confidence >= 80:
            level = ConfidenceLevel.HIGH.value
        elif final_confidence >= 70:
            level = ConfidenceLevel.MEDIUM.value
        elif final_confidence >= 50:
            level = ConfidenceLevel.LOW.value
        else:
            level = ConfidenceLevel.SUSPICIOUS.value
        
        return (final_confidence, level)
    
    @staticmethod
    def _get_baseline_confidence(
        finding_type: str,
        detection_methods: List[str],
    ) -> int:
        """Get baseline confidence based on vulnerability type and detection methods."""
        # Check if we have specific rules for this combination
        if finding_type in ConfidenceScorer.BASELINE_CONFIDENCE:
            type_rules = ConfidenceScorer.BASELINE_CONFIDENCE[finding_type]
            
            # Check for exact multi-method match
            if len(detection_methods) > 1:
                combined_key = f"{detection_methods[0]}_{detection_methods[1]}_combined"
                if combined_key in type_rules:
                    return type_rules[combined_key]
                
                # Generic combined score
                if "combined" in type_rules:
                    return type_rules["combined"]
            
            # Single method score
            if len(detection_methods) == 1:
                method = detection_methods[0]
                if method in type_rules:
                    return type_rules[method]
        
        # Default baseline confidence
        if len(detection_methods) >= 2:
            return 75  # Multiple methods = better confidence
        else:
            return 60  # Single method
    
    @staticmethod
    def _calculate_consistency_multiplier(detection_results: Dict[str, any]) -> float:
        """
        Calculate multiplier based on consistency across detection methods.
        
        Args:
            detection_results: Dictionary with detection method results
            
        Returns:
            Multiplier (0.5 to 1.2)
        """
        if not detection_results:
            return 1.0
        
        # Count positive results
        positive_count = sum(1 for v in detection_results.values() if v is True or v == "positive")
        total_count = len(detection_results)
        
        if total_count == 0:
            return 1.0
        
        consistency_ratio = positive_count / total_count
        
        # Higher consistency = higher multiplier
        if consistency_ratio >= 0.9:
            return 1.15
        elif consistency_ratio >= 0.8:
            return 1.1
        elif consistency_ratio >= 0.7:
            return 1.05
        elif consistency_ratio >= 0.5:
            return 1.0
        else:
            return 0.8  # Poor consistency reduces confidence
    
    @staticmethod
    def _calculate_factor_adjustment(additional_factors: Dict[str, any]) -> int:
        """
        Calculate adjustment to confidence based on additional factors.
        
        Args:
            additional_factors: Dictionary with optional adjustment factors
                - response_status: If unexpected, adds points
                - payload_complexity: Complex payloads increase confidence
                - reproducibility: If reproducible, adds points
                - manual_verification: If verified, adds points
            
        Returns:
            Adjustment value (-10 to +15)
        """
        adjustment = 0
        
        # Response status factor
        if additional_factors.get("response_status") == "unexpected":
            adjustment += 5
        
        # Payload complexity
        payload_complexity = additional_factors.get("payload_complexity", "normal")
        if payload_complexity == "complex":
            adjustment += 5
        elif payload_complexity == "simple":
            adjustment -= 2
        
        # Reproducibility
        if additional_factors.get("reproducible"):
            adjustment += 5
        
        # Manual verification
        if additional_factors.get("manually_verified"):
            adjustment += 10
        
        # False positive indicators
        if additional_factors.get("common_false_positive"):
            adjustment -= 10
        
        return max(-10, min(15, adjustment))
    
    @staticmethod
    def get_verification_hints(
        finding_type: str,
        endpoint: str,
        parameter: str,
        detection_method: str = "",
    ) -> List[str]:
        """
        Return manual verification steps the user can take to verify finding.
        
        Args:
            finding_type: Type of vulnerability
            endpoint: Target endpoint
            parameter: Target parameter/field
            detection_method: The detection method used
            
        Returns:
            List of verification steps
        """
        hints = {
            "SQL Injection": [
                f"1. Test with single quote (') in '{parameter}' and observe for SQL errors",
                f"2. Try boolean-based payload: {parameter}=1' AND '1'='1",
                f"3. Use time-based verification: {parameter}=1' AND SLEEP(5)--",
                f"4. Check if different payloads produce different responses",
                "5. Use UNION-based injection to extract column names",
                "6. Verify database type (MySQL, PostgreSQL, MSSQL, Oracle)",
            ],
            "Cross-Site Scripting": [
                f"1. Inject test marker in '{parameter}': {parameter}=<test123marker>",
                f"2. Check page source for unescaped marker",
                f"3. Try event handler: {parameter}=<img src=x onerror='alert(1)'>",
                f"4. Test context-specific payloads (HTML, JS, attribute)",
                "5. Check for WAF/filter bypasses (encoding, case variation)",
                "6. Verify in different browsers for consistency",
            ],
            "CSRF": [
                f"1. Identify CSRF token in form on {endpoint}",
                f"2. Check if token is required for state-changing requests",
                f"3. Try removing token and test if request still succeeds",
                f"4. Try replaying old/expired tokens",
                "5. Check if token is bound to session",
                "6. Verify CORS and Origin header validation",
            ],
            "SSRF": [
                f"1. Inject internal IP {parameter}=http://127.0.0.1:22",
                f"2. Try localhost variations: {parameter}=http://[::1]",
                f"3. Test cloud metadata: {parameter}=http://169.254.169.254/",
                f"4. Check for information disclosure in error messages",
                "5. Verify with time-based detection",
                "6. Test port scanning capabilities",
            ],
            "Authentication": [
                f"1. Test common credentials on {endpoint}",
                f"2. Check for default accounts (admin/admin, etc)",
                "3. Test password reset flow for weaknesses",
                "4. Try session fixation attacks",
                "5. Verify MFA bypass possibilities",
                "6. Check for hardcoded credentials",
            ],
            "Authorization": [
                f"1. Access {endpoint} with low-privilege account",
                f"2. Modify '{parameter}' to reference other users' data",
                "3. Check response for timing differences",
                "4. Try predictable object IDs",
                "5. Verify permission checks at API level",
                "6. Test parameter pollution",
            ],
            "Insecure Direct Object Reference": [
                f"1. Access {endpoint} with parameter {parameter}=1",
                f"2. Increment value: {parameter}=2, 3, 4, etc",
                f"3. Compare response times for authorized vs unauthorized access",
                "4. Try negative numbers or special characters",
                "5. Verify access control is enforced",
                "6. Check for direct file/resource exposure",
            ],
            "Sensitive Data Exposure": [
                f"1. Check {endpoint} response for sensitive patterns",
                f"2. Search for: credit cards, SSNs, API keys in {parameter}",
                "3. Check HTTP headers for sensitive info",
                "4. Test error messages for information disclosure",
                "5. Verify data is encrypted in transit",
                "6. Check page cache for sensitive data",
            ],
            "Path Traversal": [
                f"1. Try basic traversal in '{parameter}': ../../../etc/passwd",
                f"2. Try null byte: {parameter}=../../etc/passwd%00.jpg",
                f"3. Try encoding: %2e%2e%2f%2e%2e%2fetc%2fpasswd",
                f"4. Use application-specific paths",
                "5. Verify file exists through response comparison",
                "6. Check for logging bypasses",
            ],
            "File Upload": [
                f"1. Upload malicious file to {endpoint}",
                f"2. Check Content-Type restrictions on '{parameter}'",
                "3. Try double extensions: shell.php.jpg",
                "4. Try null bytes: shell.php%00.jpg",
                "5. Verify execution permissions",
                "6. Check uploaded file location",
            ],
            "Rate Limiting": [
                f"1. Send rapid requests to {endpoint}",
                f"2. Check for Rate-Limit-* headers",
                f"3. Verify limiting per {parameter}",
                "4. Try bypassing with X-Forwarded-For header",
                "5. Check for distributed rate limit bypass",
                "6. Verify account lockout protections",
            ],
        }
        
        return hints.get(finding_type, [
            f"1. Manually test the vulnerability on {endpoint}",
            f"2. Verify detection method: {detection_method}",
            "3. Check application behavior",
            "4. Attempt exploitation with different payloads",
            "5. Review application logs",
            "6. Test with automated tools for confirmation",
        ])
    
    @staticmethod
    def get_false_positive_risk(
        finding_type: str,
        detection_methods: List[str],
        confidence_score: int,
    ) -> float:
        """
        Calculate false positive risk (0.0 to 1.0, where 1.0 = very likely FP).
        
        Args:
            finding_type: Type of vulnerability
            detection_methods: Methods used for detection
            confidence_score: Calculated confidence score
            
        Returns:
            False positive risk as float 0-1
        """
        base_risk = 1.0 - (confidence_score / 100.0)  # Inverse of confidence
        
        # Adjust based on known false positive patterns
        method_risk = 0.0
        if len(detection_methods) == 1:
            method_risk = 0.15  # Single method is riskier
        elif len(detection_methods) >= 3:
            method_risk = -0.10  # Multiple methods reduce FP risk
        
        # Type-specific adjustments
        type_risk_adjustments = {
            "Cross-Site Scripting": 0.05,  # Generally lower FP rate
            "SQL Injection": 0.05,  # Generally lower FP rate
            "Business Logic": 0.20,  # Higher FP rate for business logic
            "Rate Limiting": 0.10,  # Can have false positives
            "Insecure Direct Object Reference": 0.10,  # Timing-based can be FP
        }
        
        type_adjustment = type_risk_adjustments.get(finding_type, 0.0)
        
        final_risk = base_risk + method_risk + type_adjustment
        return max(0.0, min(1.0, final_risk))
    
    @staticmethod
    def should_include_finding(confidence_score: int, confidence_level: str) -> bool:
        """
        Determine if finding should be included in final report.
        
        Findings with confidence >= 50% are included.
        Those < 70% are marked as 'Suspicious'.
        
        Args:
            confidence_score: Calculated confidence score (0-100)
            confidence_level: Confidence level string
            
        Returns:
            True if finding should be included, False otherwise
        """
        return confidence_score >= 50


# Predefined severity mappings for different finding types
SEVERITY_BASELINE = {
    "SQL Injection": "Critical",
    "Cross-Site Scripting": "High",
    "CSRF": "High",
    "SSRF": "High",
    "Insecure Direct Object Reference": "High",
    "Authentication": "High",
    "Authorization": "High",
    "Sensitive Data Exposure": "High",
    "Path Traversal": "High",
    "File Upload": "High",
    "Weak Cryptography": "High",
    "Command Injection": "Critical",
    "Injection": "High",
    "Security Misconfiguration": "Medium",
    "Business Logic": "Medium",
    "Rate Limiting": "Low",
}


def get_baseline_severity(finding_type: str) -> str:
    """Get baseline severity for a finding type."""
    return SEVERITY_BASELINE.get(finding_type, "Medium")
