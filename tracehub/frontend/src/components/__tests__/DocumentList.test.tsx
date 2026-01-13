import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DocumentList from '../DocumentList'
import type { Document, DocumentType } from '../../types'

// Mock date-fns format
vi.mock('date-fns', () => ({
  format: (_date: Date, _formatStr: string) => {
    // Simple mock that returns a formatted date string
    return 'Jan 15, 2026'
  }
}))

describe('DocumentList Component', () => {
  const mockDocuments: Document[] = [
    {
      id: 'doc-1',
      shipment_id: 'ship-1',
      document_type: 'bill_of_lading',
      name: 'BOL-001',
      reference_number: 'BOL-001',
      status: 'validated',
      page_count: 2,
      document_date: '2026-01-15',  // TICKET-002: Renamed from issue_date
      file_path: '/uploads/bol-001.pdf'
    },
    {
      id: 'doc-2',
      shipment_id: 'ship-1',
      document_type: 'commercial_invoice',
      name: 'Invoice-123',
      reference_number: 'INV-123',
      status: 'uploaded',
      page_count: 1,
      file_path: '/uploads/invoice-123.pdf'
    },
    {
      id: 'doc-3',
      shipment_id: 'ship-1',
      document_type: 'certificate_of_origin',
      name: 'COO-456',
      status: 'compliance_failed',
      page_count: 1
    }
  ]

  const mockCombinedDocument: Document = {
    id: 'doc-combined',
    shipment_id: 'ship-1',
    document_type: 'other',
    name: 'Combined-Docs',
    status: 'validated',
    is_combined: true,
    content_count: 3,
    page_count: 5,
    document_types: ['bill_of_lading', 'commercial_invoice', 'packing_list']
  }

  describe('Document Rendering', () => {
    it('should render list of documents', () => {
      render(<DocumentList documents={mockDocuments} />)

      expect(screen.getByText('Bill of Lading')).toBeInTheDocument()
      expect(screen.getByText('Commercial Invoice')).toBeInTheDocument()
      expect(screen.getByText('Certificate of Origin')).toBeInTheDocument()
    })

    it('should display document reference numbers', () => {
      render(<DocumentList documents={mockDocuments} />)

      expect(screen.getByText('BOL-001')).toBeInTheDocument()
      expect(screen.getByText('INV-123')).toBeInTheDocument()
    })

    it('should display page count for multi-page documents', () => {
      render(<DocumentList documents={mockDocuments} />)

      expect(screen.getByText('2 pages')).toBeInTheDocument()
    })

    it('should display issue dates', () => {
      render(<DocumentList documents={mockDocuments} />)

      expect(screen.getByText(/Issued: Jan 15, 2026/)).toBeInTheDocument()
    })
  })

  describe('Document Status', () => {
    it('should display validated status', () => {
      render(<DocumentList documents={mockDocuments} />)

      expect(screen.getByText('Validated')).toBeInTheDocument()
    })

    it('should display pending review status', () => {
      render(<DocumentList documents={mockDocuments} />)

      expect(screen.getByText('Pending Review')).toBeInTheDocument()
    })

    it('should display issues found status', () => {
      render(<DocumentList documents={mockDocuments} />)

      expect(screen.getByText('Issues Found')).toBeInTheDocument()
    })

    it('should render different status icons', () => {
      const { container } = render(<DocumentList documents={mockDocuments} />)

      // Check for different status color classes
      expect(container.querySelector('.text-success-500')).toBeInTheDocument()
      expect(container.querySelector('.text-warning-500')).toBeInTheDocument()
      expect(container.querySelector('.text-danger-500')).toBeInTheDocument()
    })
  })

  describe('Combined Documents', () => {
    it('should display combined document badge', () => {
      render(<DocumentList documents={[mockCombinedDocument]} />)

      expect(screen.getByText('3 docs')).toBeInTheDocument()
    })

    it('should show contained document types', () => {
      render(<DocumentList documents={[mockCombinedDocument]} />)

      expect(screen.getByText('Bill of Lading')).toBeInTheDocument()
      expect(screen.getByText('Commercial Invoice')).toBeInTheDocument()
      expect(screen.getByText('Packing List')).toBeInTheDocument()
    })

    it('should display layers icon for combined documents', () => {
      const { container } = render(<DocumentList documents={[mockCombinedDocument]} />)

      expect(container.querySelector('.bg-primary-100')).toBeInTheDocument()
    })
  })

  describe('Missing Documents', () => {
    const missingDocs: DocumentType[] = ['bill_of_lading', 'commercial_invoice']

    it('should display missing documents', () => {
      render(<DocumentList documents={[]} missingDocuments={missingDocs} />)

      expect(screen.getByText('Bill of Lading')).toBeInTheDocument()
      expect(screen.getByText('Commercial Invoice')).toBeInTheDocument()
      expect(screen.getAllByText('Required document missing')).toHaveLength(2)
    })

    it('should render upload buttons for missing documents', () => {
      const mockOnUpload = vi.fn()
      render(
        <DocumentList 
          documents={[]} 
          missingDocuments={missingDocs}
          onUpload={mockOnUpload}
        />
      )

      const uploadButtons = screen.getAllByText('Upload')
      expect(uploadButtons).toHaveLength(2)
    })

    it('should call onUpload when upload button clicked', async () => {
      const user = userEvent.setup()
      const mockOnUpload = vi.fn()
      
      render(
        <DocumentList 
          documents={[]} 
          missingDocuments={missingDocs}
          onUpload={mockOnUpload}
        />
      )

      const uploadButtons = screen.getAllByText('Upload')
      await user.click(uploadButtons[0])

      expect(mockOnUpload).toHaveBeenCalledWith('bill_of_lading')
    })

    it('should not show upload button when onUpload not provided', () => {
      render(<DocumentList documents={[]} missingDocuments={missingDocs} />)

      expect(screen.queryByText('Upload')).not.toBeInTheDocument()
    })
  })

  describe('Document Click Interactions', () => {
    it('should call onDocumentClick when document clicked', async () => {
      const user = userEvent.setup()
      const mockOnDocumentClick = vi.fn()
      
      render(
        <DocumentList 
          documents={mockDocuments}
          onDocumentClick={mockOnDocumentClick}
        />
      )

      const docCard = screen.getByText('Bill of Lading').closest('div')
      if (docCard) {
        await user.click(docCard)
        expect(mockOnDocumentClick).toHaveBeenCalledWith(mockDocuments[0])
      }
    })

    it('should show cursor-pointer when onDocumentClick provided', () => {
      const mockOnDocumentClick = vi.fn()
      const { container } = render(
        <DocumentList 
          documents={mockDocuments}
          onDocumentClick={mockOnDocumentClick}
        />
      )

      expect(container.querySelector('.cursor-pointer')).toBeInTheDocument()
    })

    it('should not have cursor-pointer when no onDocumentClick', () => {
      const { container } = render(<DocumentList documents={mockDocuments} />)

      expect(container.querySelector('.cursor-pointer')).not.toBeInTheDocument()
    })
  })

  describe('Horn & Hoof Documents', () => {
    const hornHoofDocs: Document[] = [
      {
        id: 'doc-traces',
        shipment_id: 'ship-1',
        document_type: 'eu_traces_certificate',
        name: 'TRACES-001',
        status: 'validated',
        reference_number: 'RC1479592'
      },
      {
        id: 'doc-vet',
        shipment_id: 'ship-1',
        document_type: 'veterinary_health_certificate',
        name: 'VET-001',
        status: 'uploaded'
      }
    ]

    it('should display horn/hoof specific documents', () => {
      render(<DocumentList documents={hornHoofDocs} />)

      expect(screen.getByText('EU TRACES Certificate')).toBeInTheDocument()
      expect(screen.getByText('Veterinary Health Certificate')).toBeInTheDocument()
    })

    it('should show TRACES registration number', () => {
      render(<DocumentList documents={hornHoofDocs} />)

      expect(screen.getByText('RC1479592')).toBeInTheDocument()
    })
  })

  describe('Empty States', () => {
    it('should show empty state when no documents', () => {
      render(<DocumentList documents={[]} />)

      expect(screen.getByText('No documents yet')).toBeInTheDocument()
    })

    it('should not show empty state when missing documents exist', () => {
      render(
        <DocumentList 
          documents={[]} 
          missingDocuments={['bill_of_lading']}
        />
      )

      expect(screen.queryByText('No documents yet')).not.toBeInTheDocument()
    })

    it('should not show empty state when documents exist', () => {
      render(<DocumentList documents={mockDocuments} />)

      expect(screen.queryByText('No documents yet')).not.toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('should handle documents without reference numbers', () => {
      const doc: Document = {
        id: 'doc-no-ref',
        shipment_id: 'ship-1',
        document_type: 'packing_list',
        name: 'Packing List',
        status: 'draft'
      }

      render(<DocumentList documents={[doc]} />)

      expect(screen.getByText('Packing List')).toBeInTheDocument()
      expect(screen.getByText('Draft')).toBeInTheDocument()
    })

    it('should handle documents without file paths', () => {
      const doc: Document = {
        id: 'doc-no-file',
        shipment_id: 'ship-1',
        document_type: 'contract',
        name: 'Contract',
        status: 'draft'
      }

      const { container } = render(<DocumentList documents={[doc]} />)

      // Should not show download button
      expect(container.querySelector('button')).not.toBeInTheDocument()
    })

    it('should handle single-page documents', () => {
      const doc: Document = {
        id: 'doc-single',
        shipment_id: 'ship-1',
        document_type: 'contract',
        name: 'Contract',
        status: 'validated',
        page_count: 1
      }

      render(<DocumentList documents={[doc]} />)

      // Should not show page count for single page
      expect(screen.queryByText('1 pages')).not.toBeInTheDocument()
    })

    it('should fallback to document_type for unknown types', () => {
      const doc: Document = {
        id: 'doc-unknown',
        shipment_id: 'ship-1',
        document_type: 'custom_type' as DocumentType,
        name: 'Custom Doc',
        status: 'draft'
      }

      render(<DocumentList documents={[doc]} />)

      expect(screen.getByText('custom_type')).toBeInTheDocument()
    })
  })
})
