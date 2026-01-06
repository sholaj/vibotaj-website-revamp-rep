/**
 * Compliance utilities for TraceHub
 *
 * Single source of truth for HS code classification and EUDR requirements.
 * Based on docs/COMPLIANCE_MATRIX.md
 */

// HS codes that require EUDR compliance (EU Deforestation Regulation)
export const EUDR_HS_CODES = ['1801', '0901', '1511', '4001', '1201'];

// Horn and hoof HS codes - explicitly NOT covered by EUDR
export const HORN_HOOF_HS_CODES = ['0506', '0507'];

/**
 * Check if EUDR (EU Deforestation Regulation) applies to an HS code.
 *
 * Horn/hoof products (HS 0506/0507) are explicitly NOT covered by EUDR.
 *
 * @param hsCode - The HS code to check (e.g., "0506", "1801.00.00")
 * @returns true if EUDR applies, false otherwise
 *
 * @example
 * isEUDRRequired("0506")     // false - Horn
 * isEUDRRequired("1801")     // true - Cocoa
 * isEUDRRequired("0714.20")  // false - Sweet potato
 */
export const isEUDRRequired = (hsCode: string): boolean => {
  if (!hsCode || !hsCode.trim()) {
    return false;
  }

  const prefix = hsCode.trim().substring(0, 4);
  return EUDR_HS_CODES.some(code => prefix.startsWith(code));
};

/**
 * Check if the HS code is for horn or hoof products.
 *
 * Horn and hoof products require special documentation
 * (EU TRACES, Veterinary Health Certificate) but NOT EUDR documents.
 *
 * @param hsCode - The HS code to check
 * @returns true if the product is horn or hoof
 */
export const isHornHoofProduct = (hsCode: string): boolean => {
  if (!hsCode || !hsCode.trim()) {
    return false;
  }

  const prefix = hsCode.trim().substring(0, 4);
  return HORN_HOOF_HS_CODES.some(code => prefix.startsWith(code));
};

/**
 * VIBOTAJ's EU TRACES registration number for animal by-products
 */
export const VIBOTAJ_TRACES_NUMBER = 'RC1479592';
