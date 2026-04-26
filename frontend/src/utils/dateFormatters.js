/**
 * Date and time formatting utilities
 */

/**
 * Format time to human readable string (HH:MM)
 * @param {string} timeStr - Time in HH:MM format
 * @returns {string}
 */
export const timeToDisplay = (timeStr) => {
  if (!timeStr) return "";
  const [hours, mins] = timeStr.split(":").map(Number);
  return `${String(hours).padStart(2, "0")}:${String(mins).padStart(2, "0")}`;
};

/**
 * Format next run timestamp to display
 * @param {string} nextRun - ISO timestamp
 * @returns {string}
 */
export const formatNextRun = (nextRun) => {
  if (!nextRun) return "Never";
  const date = new Date(nextRun);
  const now = new Date();

  // If within 24 hours, show "Tomorrow at HH:MM"
  const diff = date.getTime() - now.getTime();
  if (diff > 0 && diff < 24 * 60 * 60 * 1000) {
    const hours = String(date.getHours()).padStart(2, "0");
    const mins = String(date.getMinutes()).padStart(2, "0");
    return diff < 60 * 60 * 1000
      ? `in ${Math.round(diff / 60000)} mins`
      : `at ${hours}:${mins}`;
  }

  // Otherwise show date
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

/**
 * Format last run timestamp
 * @param {string} lastRun - ISO timestamp
 * @returns {string}
 */
export const formatLastRun = (lastRun) => {
  if (!lastRun) return "Never";
  const date = new Date(lastRun);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  // Less than 1 minute
  if (diff < 60 * 1000) return "Just now";

  // Less than 1 hour
  if (diff < 60 * 60 * 1000) {
    const mins = Math.round(diff / 60000);
    return `${mins} min${mins > 1 ? "s" : ""} ago`;
  }

  // Less than 24 hours
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.round(diff / (60 * 60 * 1000));
    return `${hours} hour${hours > 1 ? "s" : ""} ago`;
  }

  // Otherwise show date
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
};

/**
 * Get duration string from milliseconds
 * @param {number} ms - Milliseconds
 * @returns {string}
 */
export const formatDuration = (ms) => {
  if (!ms || ms < 1000) return "<1s";

  const seconds = Math.round(ms / 1000);
  if (seconds < 60) return `${seconds}s`;

  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m`;

  const hours = Math.round(minutes / 60);
  return `${hours}h`;
};

export default {
  timeToDisplay,
  formatNextRun,
  formatLastRun,
  formatDuration,
};
