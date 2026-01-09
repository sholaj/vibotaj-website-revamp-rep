import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ComplianceStatus from '../ComplianceStatus'
import type { ComplianceStatus as ComplianceStatusType, DocumentType } from '../../types'

describe('ComplianceStatus Component', () => {
  describe('Compliant State', () => {
    it('should render compliant status with all documents present', () => {
      const compliance: ComplianceStatusType = {
        is_compliant: true,
        total_required: 5,
        total_present: 5,
        missing_documents: [],
        pending_validation: [],
        issues: []
      }

      render(<ComplianceStatus compliance={compliance} />)

      expect(screen.getByText('Documentation Complete')).toBeInTheDocument()
      expect(screen.getByText('5 of 5 required documents present')).toBeInTheDocument()
      expect(screen.getByText('100%')).toBeInTheDocument()
    })

    it('should show success styling when compliant', () => {
      const compliance: ComplianceStatusType = {
        is_compliant: true,
        total_required: 3,
        total_present: 3,
        missing_documents: [],
        pending_validation: [],
        issues: []
      }

      const { container } = render(<ComplianceStatus compliance={compliance} />)

      const statusCard = container.querySelector('.bg-success-50')
      expect(statusCard).toBeInTheDocument()
    })
  })

  describe('Incomplete State', () => {
    it('should render incomplete status with missing documents', () => {
      const compliance: ComplianceStatusType = {
        is_compliant: false,
        total_required: 5,
        total_present: 3,
        missing_documents: ['bill_of_lading', 'commercial_invoice'] as DocumentType[],
        pending_validation: [],
        issues: []
      }

      render(<ComplianceStatus compliance={compliance} />)

      expect(screen.getByText('Documentation Incomplete')).toBeInTheDocument()
      expect(screen.getByText('3 of 5 required documents present')).toBeInTheDocument()
      expect(screen.getByText('60%')).toBeInTheDocument()
    })

    it('should show danger styling when incomplete', () => {
      const compliance: ComplianceStatusType = {
        is_compliant: false,
        total_required: 5,
        total_present: 2,
        missing_documents: ['bill_of_lading', 'commercial_invoice', 'packing_list'] as DocumentType[],
        pending_validation: [],
        issues: []
      }

      const { container } = render(<ComplianceStatus compliance={compliance} />)

      const statusCard = container.querySelector('.bg-danger-50')
      expect(statusCard).toBeInTheDocument()
    })

    it('should calculate correct percentage', () => {
      const compliance: ComplianceStatusType = {
        is_compliant: false,
        total_required: 8,
        total_present: 6,
        missing_documents: ['bill_of_lading', 'commercial_invoice'] as DocumentType[],
        pending_validation: [],
        issues: []
      }

      render(<ComplianceStatus compliance={compliance} />)

      expect(screen.getByText('75%')).toBeInTheDocument()
    })
  })

  describe('Missing Documents Section', () => {
    it('should display missing documents list', () => {
      const compliance: ComplianceStatusType = {
        is_compliant: false,
        total_required: 5,
        total_present: 3,
        missing_documents: ['bill_of_lading', 'commercial_invoice', 'packing_list'] as DocumentType[],
        pending_validation: [],
        issues: []
      }

      render(<ComplianceStatus compliance={compliance} />)

      expect(screen.getByText('Missing Documents')).toBeInTheDocument()
      expect(screen.getByText('Bill of Lading')).toBeInTheDocument()
      expect(screen.getByText('Commercial Invoice')).toBeInTheDocument()
      expect(screen.getByText('Packing List')).toBeInTheDocument()
    })

    it('should not show missing documents section when empty', () => {
      const compliance: ComplianceStatusType = {
        is_compliant: true,
        total_required: 3,
        total_present: 3,
        missing_documents: [],
        pending_validation: [],
        issues: []
      }

      render(<ComplianceStatus compliance={compliance} />)

      expect(screen.queryByText('Missing Documents')).not.toBeInTheDocument()
    })

    it('should display horn/hoof specific documents correctly', () => {
      const compliance: ComplianceStatusType = {
        is_compliant: false,
        total_required: 4,
        total_present: 2,
        missing_documents: ['eu_traces_certificate', 'veterinary_health_certificate'] as DocumentType[],
        pending_validation: [],
        issues: []
      }

      render(<ComplianceStatus compliance={compliance} />)

      expect(screen.getByText('EU TRACES Certificate')).toBeInTheDocument()
      expect(screen.getByText('Veterinary Health Certificate')).toBeInTheDocument()
    })
  })

  describe('Pending Validation Section', () => {
    it('should display pending validation documents', () => {
      const compliance: ComplianceStatusType = {
        is_compliant: false,
        total_required: 5,
        total_present: 3,
        missing_documents: [],
        pending_validation: ['Invoice_123.pdf', 'BOL_456.pdf'],
        issues: []
      }

      render(<ComplianceStatus compliance={compliance} />)

      expect(screen.getByText('Pending Validation')).toBeInTheDocument()
      expect(screen.getByText('Invoice_123.pdf')).toBeInTheDocument()
      expect(screen.getByText('BOL_456.pdf')).toBeInTheDocument()
    })

    it('should not show pending validation section when empty', () => {
      const compliance: ComplianceStatusType = {
        is_compliant: true,
        total_required: 3,
        total_present: 3,
        missing_documents: [],
        pending_validation: [],
        issues: []
      }

      render(<ComplianceStatus compliance={compliance} />)

      expect(screen.queryByText('Pending Validation')).not.toBeInTheDocument()
    })
  })

  describe('Issues Section', () => {
    it('should display compliance issues', () => {
      const compliance: ComplianceStatusType = {
        is_compliant: false,
        total_required: 5,
        total_present: 4,
        missing_documents: [],
        pending_validation: [],
        issues: [
          'Bill of Lading date mismatch',
          'Invoice amount exceeds purchase order',
          'Certificate of Origin expired'
        ]
      }

      render(<ComplianceStatus compliance={compliance} />)

      expect(screen.getByText('Issues')).toBeInTheDocument()
      expect(screen.getByText('Bill of Lading date mismatch')).toBeInTheDocument()
      expect(screen.getByText('Invoice amount exceeds purchase order')).toBeInTheDocument()
      expect(screen.getByText('Certificate of Origin expired')).toBeInTheDocument()
    })

    it('should not show issues section when empty', () => {
      const compliance: ComplianceStatusType = {
        is_compliant: true,
        total_required: 3,
        total_present: 3,
        missing_documents: [],
        pending_validation: [],
        issues: []
      }

      render(<ComplianceStatus compliance={compliance} />)

      expect(screen.queryByText('Issues')).not.toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('should handle zero required documents', () => {
      const compliance: ComplianceStatusType = {
        is_compliant: true,
        total_required: 0,
        total_present: 0,
        missing_documents: [],
        pending_validation: [],
        issues: []
      }

      render(<ComplianceStatus compliance={compliance} />)

      expect(screen.getByText('0 of 0 required documents present')).toBeInTheDocument()
      expect(screen.getByText('0%')).toBeInTheDocument()
    })

    it('should display all sections together when present', () => {
      const compliance: ComplianceStatusType = {
        is_compliant: false,
        total_required: 10,
        total_present: 5,
        missing_documents: ['bill_of_lading', 'commercial_invoice'] as DocumentType[],
        pending_validation: ['Draft_Invoice.pdf'],
        issues: ['Expired certificate', 'Missing signature']
      }

      render(<ComplianceStatus compliance={compliance} />)

      expect(screen.getByText('Missing Documents')).toBeInTheDocument()
      expect(screen.getByText('Pending Validation')).toBeInTheDocument()
      expect(screen.getByText('Issues')).toBeInTheDocument()
      expect(screen.getByText('50%')).toBeInTheDocument()
    })

    it('should round percentage correctly', () => {
      const compliance: ComplianceStatusType = {
        is_compliant: false,
        total_required: 3,
        total_present: 2,
        missing_documents: ['bill_of_lading'] as DocumentType[],
        pending_validation: [],
        issues: []
      }

      render(<ComplianceStatus compliance={compliance} />)

      // 2/3 = 66.666... should round to 67%
      expect(screen.getByText('67%')).toBeInTheDocument()
    })
  })
})
