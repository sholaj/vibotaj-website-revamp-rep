import { describe, it, expect } from 'vitest'
import { isEUDRRequired, isHornHoofProduct, EUDR_HS_CODES, HORN_HOOF_HS_CODES, VIBOTAJ_TRACES_NUMBER } from '../compliance'

describe('Compliance Utilities', () => {
  describe('isEUDRRequired', () => {
    it('should return true for EUDR-covered HS codes', () => {
      expect(isEUDRRequired('1801')).toBe(true)
      expect(isEUDRRequired('1801.00.00')).toBe(true)
      expect(isEUDRRequired('0901')).toBe(true)
      expect(isEUDRRequired('0901.21')).toBe(true)
      expect(isEUDRRequired('1511')).toBe(true)
      expect(isEUDRRequired('4001')).toBe(true)
      expect(isEUDRRequired('1201')).toBe(true)
    })

    it('should return false for horn/hoof products', () => {
      expect(isEUDRRequired('0506')).toBe(false)
      expect(isEUDRRequired('0506.10')).toBe(false)
      expect(isEUDRRequired('0507')).toBe(false)
      expect(isEUDRRequired('0507.90')).toBe(false)
    })

    it('should return false for non-EUDR HS codes', () => {
      expect(isEUDRRequired('0714')).toBe(false)
      expect(isEUDRRequired('0714.20')).toBe(false)
      expect(isEUDRRequired('1234')).toBe(false)
      expect(isEUDRRequired('9999')).toBe(false)
    })

    it('should handle edge cases', () => {
      expect(isEUDRRequired('')).toBe(false)
      expect(isEUDRRequired('  ')).toBe(false)
      expect(isEUDRRequired('abc')).toBe(false)
    })

    it('should handle whitespace', () => {
      expect(isEUDRRequired('  1801  ')).toBe(true)
      expect(isEUDRRequired(' 0506 ')).toBe(false)
    })
  })

  describe('isHornHoofProduct', () => {
    it('should return true for horn/hoof HS codes', () => {
      expect(isHornHoofProduct('0506')).toBe(true)
      expect(isHornHoofProduct('0506.10')).toBe(true)
      expect(isHornHoofProduct('0506.90.00')).toBe(true)
      expect(isHornHoofProduct('0507')).toBe(true)
      expect(isHornHoofProduct('0507.10')).toBe(true)
      expect(isHornHoofProduct('0507.90.00')).toBe(true)
    })

    it('should return false for EUDR-covered products', () => {
      expect(isHornHoofProduct('1801')).toBe(false)
      expect(isHornHoofProduct('0901')).toBe(false)
      expect(isHornHoofProduct('1511')).toBe(false)
    })

    it('should return false for other HS codes', () => {
      expect(isHornHoofProduct('0714')).toBe(false)
      expect(isHornHoofProduct('1234')).toBe(false)
      expect(isHornHoofProduct('9999')).toBe(false)
    })

    it('should handle edge cases', () => {
      expect(isHornHoofProduct('')).toBe(false)
      expect(isHornHoofProduct('  ')).toBe(false)
      expect(isHornHoofProduct('abc')).toBe(false)
    })

    it('should handle whitespace', () => {
      expect(isHornHoofProduct('  0506  ')).toBe(true)
      expect(isHornHoofProduct(' 1801 ')).toBe(false)
    })
  })

  describe('Constants', () => {
    it('should have correct EUDR HS codes', () => {
      expect(EUDR_HS_CODES).toEqual(['1801', '0901', '1511', '4001', '1201'])
    })

    it('should have correct horn/hoof HS codes', () => {
      expect(HORN_HOOF_HS_CODES).toEqual(['0506', '0507'])
    })

    it('should have VIBOTAJ TRACES number', () => {
      expect(VIBOTAJ_TRACES_NUMBER).toBe('RC1479592')
    })
  })

  describe('Integration', () => {
    it('should never have HS codes in both EUDR and horn/hoof lists', () => {
      const overlap = EUDR_HS_CODES.filter(code => HORN_HOOF_HS_CODES.includes(code))
      expect(overlap).toHaveLength(0)
    })

    it('should correctly classify all predefined codes', () => {
      // EUDR codes should be EUDR, not horn/hoof
      EUDR_HS_CODES.forEach(code => {
        expect(isEUDRRequired(code)).toBe(true)
        expect(isHornHoofProduct(code)).toBe(false)
      })

      // Horn/hoof codes should be horn/hoof, not EUDR
      HORN_HOOF_HS_CODES.forEach(code => {
        expect(isHornHoofProduct(code)).toBe(true)
        expect(isEUDRRequired(code)).toBe(false)
      })
    })
  })
})
