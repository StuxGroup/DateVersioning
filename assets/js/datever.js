/* Date Versioning - the "Next version" and "Validate" tools. No dependencies.
   Uses the regular expression from the specification (injected at build time from SPEC.md into
   #datever-data) plus a real-calendar-date check (rule 2).
   Copyright (c) 2026 Stux.Group. All rights reserved. */
(function () {
  "use strict";

  var data = JSON.parse(document.getElementById("datever-data").textContent);
  var RE = new RegExp(data.regex.named);
  var MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

  function pad(n) { return (n < 10 ? "0" : "") + n; }
  // Gregorian calendar, for any year (Date only goes up to the year 275760).
  function isLeap(y) { return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0; }
  function daysIn(year, month) { return month === 2 ? (isLeap(year) ? 29 : 28) : [31, 0, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]; }
  function $(id) { return document.getElementById(id); }

  // Today's UTC date as {y, m, d} (y is the full year).
  function todayUTC() {
    var n = new Date();
    return { y: n.getUTCFullYear(), m: n.getUTCMonth() + 1, d: n.getUTCDate() };
  }
  // YY up to 2099, the full year from 2100 (rule 12).
  function fmtYear(y) { return y <= 2099 ? pad(y - 2000) : String(y); }
  function fmtDate(dt) { return fmtYear(dt.y) + "." + pad(dt.m) + "." + pad(dt.d); }
  function dateKey(dt) { return dt.y * 10000 + dt.m * 100 + dt.d; }
  function longDate(dt) { return dt.d + " " + MONTHS[dt.m - 1] + " " + dt.y; }

  // Explain why a string that fails the regular expression is not a Date Version.
  function whyNot(s) {
    if (s === "") return "Enter a version to check.";
    if (/^v/i.test(s)) return "A version has no prefix (rule 11). A leading v is only for tag names: write 26.10.01, tag it v26.10.01.";
    if (/\s/.test(s)) return "A version cannot contain whitespace.";
    var m = s.match(/^(\d+)\.(\d+)\.(\d+)(?:-(\d+))?(?:\+(.*))?$/);
    if (!m) {
      if (/^\d+\.\d+$/.test(s)) return "A version needs three parts, YY.MM.DD (rule 2).";
      if (/^\d+\.\d+\.\d+-/.test(s)) return "The suffix must be -N, a release number (rule 6). Date Versioning has no pre-release syntax; use build metadata such as +beta.1 if you need a label.";
      if (/^\d+\.\d+\.\d+\+/.test(s)) return "Build metadata must be dot-separated identifiers of ASCII letters, digits and hyphens, none empty (rule 8).";
      return "Not in the form YY.MM.DD, YY.MM.DD-N or either with +build (rules 2, 5, 6 and 8).";
    }
    if (m[1].length === 4 && +m[1] >= 2000 && +m[1] <= 2099) {
      return "The years 2000 to 2099 are written as YY, not in full: " + m[1].slice(2) + "." + m[2] + "." + m[3] + ", not " + m[1] + "." + m[2] + "." + m[3] + " (rule 12).";
    }
    if (m[1].length >= 4 && /^0/.test(m[1])) return "A full year has no leading zeros (rule 12).";
    if (m[1].length >= 4 && +m[1] < 2000) return "Date Versions start in the year 2000 (rule 2).";
    if (m[1].length !== 2 && m[1].length < 4) return "The year is YY (two digits, up to 2099) or the full year (from 2100) (rules 2 and 12).";
    if (m[2].length !== 2 || m[3].length !== 2) {
      return "MM and DD must be exactly two digits, zero-padded (26.10.01, never 26.10.1) (rule 2).";
    }
    if (+m[2] < 1 || +m[2] > 12) return "The month MM must be from 01 to 12 (rule 2).";
    if (+m[3] < 1 || +m[3] > 31) return "The day DD must be from 01 to 31 (rule 2).";
    if (m[4] !== undefined) {
      if (/^0+$/.test(m[4])) return "The release number N cannot be 0: the second release of the day is -1 (rule 6).";
      if (/^0/.test(m[4])) return "The release number N cannot have leading zeros (rule 6).";
    }
    if (m[5] !== undefined) return "Build metadata must be dot-separated identifiers of ASCII letters, digits and hyphens, none empty (rule 8).";
    return "Not a valid Date Version.";
  }

  // Parse a version. Returns {ok:true, y, m, d, n, build} or {ok:false, reason}.
  function parse(raw) {
    var s = raw.trim();
    var m = RE.exec(s);
    if (!m) return { ok: false, reason: whyNot(s) };
    // YY is the year 20YY; a full year (from 2100) is the year itself (rules 2 and 12).
    var y = m[1].length === 2 ? 2000 + parseInt(m[1], 10) : parseInt(m[1], 10), mo = parseInt(m[2], 10), d = parseInt(m[3], 10);
    var dim = daysIn(y, mo);
    if (d > dim) {
      return { ok: false, reason: fmtYear(y) + "." + pad(mo) + "." + pad(d) + " is not a real calendar date: " + MONTHS[mo - 1] + " " + y + " has only " + dim + " days (rule 2)." };
    }
    return { ok: true, y: y, m: mo, d: d, n: m[4] === undefined ? 0 : parseInt(m[4], 10), build: m[5] || "", releaseText: m[4] };
  }

  function canonical(v) { return fmtDate(v) + (v.n > 0 ? "-" + v.n : ""); }

  // SemVer form (spec: Compatibility with Semantic Versioning). null when N > 99.
  function semver(v) {
    if (v.n > 99) return null;
    return (v.y - 2000) + "." + v.m + "." + (v.d * 100 + v.n) + (v.build ? "+" + v.build : "");
  }

  // ---- Next version ----
  var nvLatest = $("nv-latest"), nvDate = $("nv-date"), nvToday = $("nv-today"), nvNext = $("nv-next"), nvNote = $("nv-note");

  function pickedDate() {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(nvDate.value);
    if (!m) return null;
    return { y: +m[1], m: +m[2], d: +m[3] };
  }

  function updateNext() {
    var today = todayUTC();
    nvToday.textContent = fmtDate(today);
    var when = pickedDate() || today;
    if (when.y < 2000) {
      nvNext.textContent = "—";
      nvNote.textContent = "Date Versions start in the year 2000 (rule 2).";
      return;
    }
    var raw = nvLatest.value.trim();
    if (raw === "") {
      nvNext.textContent = fmtDate(when);
      nvNote.textContent = "No latest version given, so this is the first release on " + longDate(when) + " (UTC).";
      return;
    }
    var latest = parse(raw);
    if (!latest.ok) {
      nvNext.textContent = "—";
      nvNote.textContent = "The latest version is not valid: " + latest.reason;
      return;
    }
    var lk = dateKey(latest), wk = dateKey(when);
    if (lk > wk) {
      var fut = { y: latest.y, m: latest.m, d: latest.d, n: latest.n + 1 };
      nvNext.textContent = canonical(fut);
      nvNote.textContent = "Your latest version is dated after " + longDate(when) + ". The next release must still rank above it (rule 7), so it stays on that date with the next release number.";
      return;
    }
    if (lk === wk) {
      var same = { y: when.y, m: when.m, d: when.d, n: latest.n + 1 };
      nvNext.textContent = canonical(same);
      nvNote.textContent = "The latest version is already on " + longDate(when) + ", so this is release " + same.n + " of that day.";
      return;
    }
    nvNext.textContent = fmtDate(when);
    nvNote.textContent = "The latest version is from an earlier date, so the first release on " + longDate(when) + " (UTC) needs no suffix.";
  }

  // ---- Validate ----
  var valInput = $("val-input"), valStatus = $("val-status"), valReason = $("val-reason"),
      valSemRow = $("val-semver-row"), valSem = $("val-semver"), valDetail = $("val-detail");

  function updateValidate() {
    var v = parse(valInput.value);
    if (!v.ok) {
      var empty = valInput.value.trim() === "";
      valStatus.textContent = empty ? "" : "Invalid";
      valStatus.setAttribute("data-valid", empty ? "" : "false");
      valReason.textContent = v.reason;
      valSemRow.hidden = true;
      valSem.textContent = "";
      valDetail.textContent = "";
      return;
    }
    valStatus.textContent = "Valid";
    valStatus.setAttribute("data-valid", "true");
    valReason.textContent = "";
    var notes = [];
    notes.push("Released on " + longDate(v) + " (UTC), " + (v.n === 0 ? "the first release of the day" : "release number " + v.n + ", after " + v.n + " earlier release" + (v.n === 1 ? "" : "s") + " that day") + ".");
    if (v.build) notes.push("Build metadata (+" + v.build + ") is ignored for precedence.");
    var today = todayUTC();
    if (dateKey(v) > dateKey(today)) notes.push("Warning: this date is in the future, and a version must not carry a future date (rule 3).");
    var sv = semver(v);
    if (sv === null) {
      valSemRow.hidden = true;
      valSem.textContent = "";
      notes.push("No SemVer form: release numbers above 99 do not fit (the highest is -99).");
    } else {
      valSemRow.hidden = false;
      valSem.textContent = sv;
      notes.push("If your project declares a major offset (rule 13), add it to the first number of the SemVer form.");
    }
    valDetail.textContent = notes.join(" ");
  }

  nvLatest.addEventListener("input", updateNext);
  nvDate.addEventListener("input", updateNext);
  valInput.addEventListener("input", updateValidate);
  $("next-tool").addEventListener("submit", function (e) { e.preventDefault(); });
  $("validate-tool").addEventListener("submit", function (e) { e.preventDefault(); });

  var t = todayUTC();
  nvDate.value = t.y + "-" + pad(t.m) + "-" + pad(t.d);
  updateNext();
  updateValidate();
})();
