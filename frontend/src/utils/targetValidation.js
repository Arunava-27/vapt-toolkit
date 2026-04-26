/**
 * Target validation utilities
 * Extracted from ScopeEditor.jsx
 */

/**
 * Infer target type from string
 * @param {string} target - Target string
 * @returns {string} - 'ip', 'domain', 'url', or 'unknown'
 */
export const inferTargetType = (target) => {
  if (!target) return "unknown";

  target = target.trim();

  // URLs
  if (target.startsWith("http://") || target.startsWith("https://")) {
    return "url";
  }

  // IPv4
  const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
  if (ipv4Regex.test(target)) {
    const octets = target.split(".").map(Number);
    if (octets.every((o) => o >= 0 && o <= 255)) {
      return "ip";
    }
  }

  // CIDR notation
  if (target.includes("/")) {
    const [ip, bits] = target.split("/");
    if (ipv4Regex.test(ip) && !isNaN(bits) && bits >= 0 && bits <= 32) {
      return "ip";
    }
  }

  // Domain (contains dot and no spaces)
  if (target.includes(".") && !target.includes(" ")) {
    return "domain";
  }

  return "unknown";
};

/**
 * Validate target against rules
 * @param {string} target - Target to validate
 * @returns {object} - { valid: boolean, error?: string }
 */
export const validateTarget = (target) => {
  target = (target || "").trim();

  if (!target) {
    return { valid: false, error: "Target cannot be empty" };
  }

  const type = inferTargetType(target);

  if (type === "unknown") {
    return { valid: false, error: "Invalid target. Must be: IP address, domain name, or HTTP(S) URL" };
  }

  // Additional validations per type
  if (type === "ip") {
    if (target.includes("/")) {
      const [ip, bits] = target.split("/");
      const bitsNum = parseInt(bits);
      if (bitsNum < 8 || bitsNum > 32) {
        return { valid: false, error: "CIDR bits must be between 8 and 32" };
      }
    }
  }

  if (type === "domain") {
    if (target.length > 255) {
      return { valid: false, error: "Domain too long (max 255 characters)" };
    }
    if (!target.match(/^[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}$/)) {
      return { valid: false, error: "Invalid domain format" };
    }
  }

  if (type === "url") {
    try {
      new URL(target);
    } catch {
      return { valid: false, error: "Invalid URL format" };
    }
  }

  return { valid: true };
};

/**
 * Check if two targets are similar (probably duplicates)
 * @param {string} target1
 * @param {string} target2
 * @returns {boolean}
 */
export const areSimilarTargets = (target1, target2) => {
  target1 = (target1 || "").trim().toLowerCase();
  target2 = (target2 || "").trim().toLowerCase();

  if (target1 === target2) return true;

  // Add http:// and https:// variants as duplicates
  const normalize = (t) => {
    if (t.startsWith("http://")) return t.slice(7);
    if (t.startsWith("https://")) return t.slice(8);
    return t;
  };

  return normalize(target1) === normalize(target2);
};

export default {
  inferTargetType,
  validateTarget,
  areSimilarTargets,
};
