import type { Money } from "./types";

export type MoneyParseErrorCode =
  | "empty"
  | "invalid_format"
  | "too_many_decimals"
  | "unsafe_amount"
  | "invalid_scale";

export type MoneyParseResult =
  | { ok: true; amountMinor: number }
  | { ok: false; code: MoneyParseErrorCode; message: string };

/**
 * A FinancialPeriod scale is a display/import unit, never a second Money
 * exponent.  The editor parses directly into actual minor units using the
 * selected display scale.
 */
export type MoneyDisplayScale = "whole" | "thousands" | "millions";

export function displayScaleDigits(scale: MoneyDisplayScale): number {
  return scale === "millions" ? 6 : scale === "thousands" ? 3 : 0;
}

function message(code: MoneyParseErrorCode, zh: boolean): string {
  const copy = zh
    ? {
        empty: "金額不得留白。",
        invalid_format: "請輸入一般十進位金額；不接受科學記號。",
        too_many_decimals: "小數位數超過此幣別允許的精度。",
        unsafe_amount: "金額超過目前瀏覽器可精確處理的上限。",
        invalid_scale: "幣別精度設定無效。",
      }
    : {
        empty: "Amount is required.",
        invalid_format:
          "Enter a standard decimal amount; scientific notation is not accepted.",
        too_many_decimals:
          "The amount has more decimal places than this currency allows.",
        unsafe_amount:
          "The amount exceeds the exact range supported by this browser.",
        invalid_scale: "The currency scale is invalid.",
      };
  return copy[code];
}

export function parseMoneyInput(
  input: string,
  exponent = 2,
  language: "en" | "zh-TW" = "en",
): MoneyParseResult {
  const zh = language === "zh-TW";
  // USD cents displayed in millions require eight decimal places to preserve
  // an arbitrary cent value through an edit/save/reload round trip.
  if (!Number.isInteger(exponent) || exponent < 0 || exponent > 8) {
    return {
      ok: false,
      code: "invalid_scale",
      message: message("invalid_scale", zh),
    };
  }

  const trimmed = input.trim();
  if (trimmed === "") {
    return { ok: false, code: "empty", message: message("empty", zh) };
  }
  if (/[eE]/.test(trimmed)) {
    return {
      ok: false,
      code: "invalid_format",
      message: message("invalid_format", zh),
    };
  }

  const unsigned = trimmed.startsWith("-") ? trimmed.slice(1) : trimmed;
  const [wholePart = "", fraction = "", ...extra] = unsigned.split(".");
  const groupingValid =
    /^\d+$/.test(wholePart) || /^\d{1,3}(,\d{3})+$/.test(wholePart);
  if (!groupingValid || extra.length > 0 || !/^\d*$/.test(fraction)) {
    return {
      ok: false,
      code: "invalid_format",
      message: message("invalid_format", zh),
    };
  }
  if (fraction.length > exponent) {
    return {
      ok: false,
      code: "too_many_decimals",
      message: message("too_many_decimals", zh),
    };
  }

  const whole = wholePart.replaceAll(",", "");
  const digits = `${whole}${fraction.padEnd(exponent, "0")}`.replace(
    /^0+(?=\d)/,
    "",
  );
  const signed = BigInt(digits || "0") * (trimmed.startsWith("-") ? -1n : 1n);
  if (
    signed > BigInt(Number.MAX_SAFE_INTEGER) ||
    signed < BigInt(Number.MIN_SAFE_INTEGER)
  ) {
    return {
      ok: false,
      code: "unsafe_amount",
      message: message("unsafe_amount", zh),
    };
  }
  return { ok: true, amountMinor: Number(signed) };
}

/**
 * Normalize a value entered in a period's display unit into canonical
 * `Money.amount_minor` units exactly once.
 *
 * For USD, `100.00` means 100 dollars at `whole`, 100 thousand dollars at
 * `thousands`, and 100 million dollars at `millions`.  Parsing at the
 * expanded exponent avoids lossy Number multiplication and also preserves
 * values such as 0.00010001 million (= $100.01).
 */
export function normalizeMoneyInput(
  input: string,
  displayScale: MoneyDisplayScale,
  baseExponent = 2,
  language: "en" | "zh-TW" = "en",
): MoneyParseResult {
  return parseMoneyInput(
    input,
    baseExponent + displayScaleDigits(displayScale),
    language,
  );
}

export function formatMoneyInput(value: Money): string {
  const minor = BigInt(value.amount_minor);
  const scale = 10n ** BigInt(value.minor_unit_exponent);
  const negative = minor < 0n;
  const absolute = negative ? -minor : minor;
  const whole = absolute / scale;
  if (value.minor_unit_exponent === 0) return `${negative ? "-" : ""}${whole}`;
  const fraction = (absolute % scale)
    .toString()
    .padStart(value.minor_unit_exponent, "0");
  return `${negative ? "-" : ""}${whole}.${fraction}`;
}

/**
 * Render canonical actual minor units in a period's display unit without
 * converting through JavaScript Number arithmetic.
 */
export function formatMoneyAtScale(
  value: Money,
  displayScale: MoneyDisplayScale,
): string {
  const digits = displayScaleDigits(displayScale);
  if (digits === 0) return formatMoneyInput(value);

  const minor = BigInt(value.amount_minor);
  const denominator = 10n ** BigInt(value.minor_unit_exponent + digits);
  const negative = minor < 0n;
  const absolute = negative ? -minor : minor;
  const whole = absolute / denominator;
  const minimumFractionDigits = value.minor_unit_exponent;
  let fraction = (absolute % denominator)
    .toString()
    .padStart(value.minor_unit_exponent + digits, "0");
  while (fraction.length > minimumFractionDigits && fraction.endsWith("0")) {
    fraction = fraction.slice(0, -1);
  }
  if (minimumFractionDigits > 0 && fraction.length === 0) {
    fraction = "0".repeat(minimumFractionDigits);
  }
  return `${negative ? "-" : ""}${whole}.${fraction}`;
}
