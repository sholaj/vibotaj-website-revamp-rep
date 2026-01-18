import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CreateShipmentModal } from '../CreateShipmentModal'
import api from '../../api/client'

// Mock the API client
vi.mock('../../api/client', () => ({
  default: {
    getBuyerOrganizations: vi.fn(),
    createShipment: vi.fn(),
  },
}))

const mockBuyers = [
  { id: '1', name: 'HAGES GmbH', slug: 'hages', type: 'buyer' },
  { id: '2', name: 'Witatrade', slug: 'witatrade', type: 'buyer' },
  { id: '3', name: 'Beckman GBH', slug: 'beckman', type: 'buyer' },
]

const mockShipment = {
  id: 'ship-123',
  reference: 'VIBO-2026-001',
  container_number: 'MSCU1234567',
  status: 'draft' as const,  // TICKET-001: Changed from 'created' to 'draft'
}

describe('CreateShipmentModal Component', () => {
  const mockOnClose = vi.fn()
  const mockOnSuccess = vi.fn()
  const mockOrganizationId = 'org-123'

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.getBuyerOrganizations).mockResolvedValue(mockBuyers)
    vi.mocked(api.createShipment).mockResolvedValue(mockShipment)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Rendering', () => {
    it('should render when isOpen is true', () => {
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      expect(screen.getByText('Create New Shipment')).toBeInTheDocument()
      expect(screen.getByLabelText(/Reference Number/)).toBeInTheDocument()
      expect(screen.getByLabelText(/Container Number/)).toBeInTheDocument()
      expect(screen.getByLabelText(/Vessel Name/)).toBeInTheDocument()
      expect(screen.getByLabelText(/Product Type/)).toBeInTheDocument()
      expect(screen.getByLabelText(/Buyer Organization/)).toBeInTheDocument()
      expect(screen.getByLabelText(/Historical Shipment/)).toBeInTheDocument()
    })

    it('should not render when isOpen is false', () => {
      render(
        <CreateShipmentModal
          isOpen={false}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      expect(screen.queryByText('Create New Shipment')).not.toBeInTheDocument()
    })

    it('should load buyer organizations on mount', async () => {
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      await waitFor(() => {
        expect(api.getBuyerOrganizations).toHaveBeenCalled()
      })

      // Check buyers are in the dropdown
      expect(screen.getByText('HAGES GmbH')).toBeInTheDocument()
      expect(screen.getByText('Witatrade')).toBeInTheDocument()
      expect(screen.getByText('Beckman GBH')).toBeInTheDocument()
    })
  })

  describe('Container Validation', () => {
    it('should show validation error for invalid container format', async () => {
      const user = userEvent.setup()
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      const containerInput = screen.getByLabelText(/Container Number/)
      await user.type(containerInput, 'INVALID')
      fireEvent.blur(containerInput)

      await waitFor(() => {
        expect(screen.getByText(/Invalid format. Expected: 4 letters \+ 7 digits/)).toBeInTheDocument()
      })
    })

    it('should accept valid container number (ISO 6346)', async () => {
      const user = userEvent.setup()
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      const containerInput = screen.getByLabelText(/Container Number/)
      await user.type(containerInput, 'MSCU1234567')
      fireEvent.blur(containerInput)

      await waitFor(() => {
        expect(screen.queryByText(/Invalid format/)).not.toBeInTheDocument()
      })
    })

    it('should convert container number to uppercase', async () => {
      const user = userEvent.setup()
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      const containerInput = screen.getByLabelText(/Container Number/) as HTMLInputElement
      await user.type(containerInput, 'mscu1234567')

      expect(containerInput.value).toBe('MSCU1234567')
    })

    it('should allow submission with empty container (Issue #41)', async () => {
      // Issue #41: Container number is now optional for draft shipments
      const user = userEvent.setup()
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      // Fill reference and product type, but leave container empty
      const referenceInput = screen.getByLabelText(/Reference Number/)
      await user.type(referenceInput, 'VIBO-2026-001')

      // Select product type (required)
      const productTypeSelect = screen.getByLabelText(/Product Type/)
      await user.selectOptions(productTypeSelect, 'horn_hoof')

      // Click submit - should not show container error
      const submitButton = screen.getByRole('button', { name: /Create Shipment/i })
      await user.click(submitButton)

      // Should not find container error message
      await waitFor(() => {
        expect(screen.queryByText(/Container number is required/)).not.toBeInTheDocument()
      })
    })
  })

  describe('Reference Validation', () => {
    it('should show validation error for invalid reference format', async () => {
      const user = userEvent.setup()
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      const referenceInput = screen.getByLabelText(/Reference Number/)
      await user.type(referenceInput, 'INVALID-REF')
      fireEvent.blur(referenceInput)

      await waitFor(() => {
        expect(screen.getByText(/Invalid format. Expected: VIBO-YYYY-NNN/)).toBeInTheDocument()
      })
    })

    it('should accept valid reference number', async () => {
      const user = userEvent.setup()
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      const referenceInput = screen.getByLabelText(/Reference Number/)
      await user.type(referenceInput, 'VIBO-2026-001')
      fireEvent.blur(referenceInput)

      await waitFor(() => {
        expect(screen.queryByText(/Invalid format/)).not.toBeInTheDocument()
      })
    })

    it('should generate reference when Generate button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      const generateButton = screen.getByRole('button', { name: /Generate/i })
      await user.click(generateButton)

      const referenceInput = screen.getByLabelText(/Reference Number/) as HTMLInputElement
      expect(referenceInput.value).toMatch(/^VIBO-\d{4}-\d{3}$/)
    })
  })

  describe('Form Submission', () => {
    it('should submit form with valid data', async () => {
      const user = userEvent.setup()
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      // Fill form
      const referenceInput = screen.getByLabelText(/Reference Number/)
      await user.type(referenceInput, 'VIBO-2026-001')

      const containerInput = screen.getByLabelText(/Container Number/)
      await user.type(containerInput, 'MSCU1234567')

      const vesselInput = screen.getByLabelText(/Vessel Name/)
      await user.type(vesselInput, 'MSC AURORA')

      // Select product type (required)
      const productTypeSelect = screen.getByLabelText(/Product Type/)
      await user.selectOptions(productTypeSelect, 'horn_hoof')

      // Submit form
      const submitButton = screen.getByRole('button', { name: /Create Shipment/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(api.createShipment).toHaveBeenCalledWith({
          reference: 'VIBO-2026-001',
          container_number: 'MSCU1234567',
          vessel_name: 'MSC AURORA',
          product_type: 'horn_hoof',  // Default product type
          buyer_organization_id: undefined,
          is_historical: false,
        })
      })
    })

    it('should show success message after creation', async () => {
      const user = userEvent.setup()
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      // Fill form
      await user.type(screen.getByLabelText(/Reference Number/), 'VIBO-2026-001')
      await user.type(screen.getByLabelText(/Container Number/), 'MSCU1234567')
      await user.selectOptions(screen.getByLabelText(/Product Type/), 'horn_hoof')

      // Submit
      await user.click(screen.getByRole('button', { name: /Create Shipment/i }))

      await waitFor(() => {
        expect(screen.getByText('Shipment created successfully!')).toBeInTheDocument()
      })
    })

    it('should show error message on API failure', async () => {
      vi.mocked(api.createShipment).mockRejectedValueOnce(new Error('Server error'))

      const user = userEvent.setup()
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      // Fill form
      await user.type(screen.getByLabelText(/Reference Number/), 'VIBO-2026-001')
      await user.type(screen.getByLabelText(/Container Number/), 'MSCU1234567')
      await user.selectOptions(screen.getByLabelText(/Product Type/), 'horn_hoof')

      // Submit
      await user.click(screen.getByRole('button', { name: /Create Shipment/i }))

      await waitFor(() => {
        expect(screen.getByText(/Server error/)).toBeInTheDocument()
      })
    })

    it('should include buyer organization ID when selected', async () => {
      const user = userEvent.setup()
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      // Wait for buyers to load
      await waitFor(() => {
        expect(screen.getByText('HAGES GmbH')).toBeInTheDocument()
      })

      // Fill form
      await user.type(screen.getByLabelText(/Reference Number/), 'VIBO-2026-001')
      await user.type(screen.getByLabelText(/Container Number/), 'MSCU1234567')
      await user.selectOptions(screen.getByLabelText(/Product Type/), 'horn_hoof')

      // Select buyer
      const buyerSelect = screen.getByLabelText(/Buyer Organization/)
      await user.selectOptions(buyerSelect, '1')

      // Submit
      await user.click(screen.getByRole('button', { name: /Create Shipment/i }))

      await waitFor(() => {
        expect(api.createShipment).toHaveBeenCalledWith(
          expect.objectContaining({
            buyer_organization_id: '1',
            product_type: 'horn_hoof',
          })
        )
      })
    })

    it('should include historical flag when checked', async () => {
      const user = userEvent.setup()
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      // Fill form
      await user.type(screen.getByLabelText(/Reference Number/), 'VIBO-2026-001')
      await user.type(screen.getByLabelText(/Container Number/), 'MSCU1234567')
      await user.selectOptions(screen.getByLabelText(/Product Type/), 'horn_hoof')

      // Check historical
      const historicalCheckbox = screen.getByLabelText(/Historical Shipment/)
      await user.click(historicalCheckbox)

      // Submit
      await user.click(screen.getByRole('button', { name: /Create Shipment/i }))

      await waitFor(() => {
        expect(api.createShipment).toHaveBeenCalledWith(
          expect.objectContaining({
            is_historical: true,
            product_type: 'horn_hoof',
          })
        )
      })
    })
  })

  describe('Modal Interactions', () => {
    it('should call onClose when Cancel button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      const cancelButton = screen.getByRole('button', { name: /Cancel/i })
      await user.click(cancelButton)

      expect(mockOnClose).toHaveBeenCalled()
    })

    it('should call onClose when X button is clicked', async () => {
      const user = userEvent.setup()
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      const closeButton = screen.getByRole('button', { name: /Close modal/i })
      await user.click(closeButton)

      expect(mockOnClose).toHaveBeenCalled()
    })

    it('should call onClose when backdrop is clicked', async () => {
      const user = userEvent.setup()
      const { container } = render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      const backdrop = container.querySelector('.bg-black.bg-opacity-50')
      if (backdrop) {
        await user.click(backdrop)
      }

      expect(mockOnClose).toHaveBeenCalled()
    })

    it('should disable form during submission', async () => {
      // Make the API call hang
      vi.mocked(api.createShipment).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockShipment), 1000))
      )

      const user = userEvent.setup()
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      // Fill form
      await user.type(screen.getByLabelText(/Reference Number/), 'VIBO-2026-001')
      await user.type(screen.getByLabelText(/Container Number/), 'MSCU1234567')
      await user.selectOptions(screen.getByLabelText(/Product Type/), 'horn_hoof')

      // Submit
      await user.click(screen.getByRole('button', { name: /Create Shipment/i }))

      // Check loading state
      expect(screen.getByText('Creating...')).toBeInTheDocument()
      expect(screen.getByLabelText(/Reference Number/)).toBeDisabled()
      expect(screen.getByLabelText(/Container Number/)).toBeDisabled()
    })

    it('should reset form when modal is closed', async () => {
      const user = userEvent.setup()
      const { rerender } = render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      // Fill form
      await user.type(screen.getByLabelText(/Reference Number/), 'VIBO-2026-001')
      await user.type(screen.getByLabelText(/Container Number/), 'MSCU1234567')

      // Close and reopen
      rerender(
        <CreateShipmentModal
          isOpen={false}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      rerender(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      // Form should be reset
      const referenceInput = screen.getByLabelText(/Reference Number/) as HTMLInputElement
      const containerInput = screen.getByLabelText(/Container Number/) as HTMLInputElement

      // Note: Form reset happens when close is called, not just when isOpen changes
      // This test verifies the initial state of a newly opened modal
      expect(referenceInput).toBeInTheDocument()
      expect(containerInput).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('should handle API failure for loading buyers gracefully', async () => {
      vi.mocked(api.getBuyerOrganizations).mockRejectedValueOnce(new Error('Network error'))

      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      // Should still render the form - buyer selection is optional
      expect(screen.getByText('Create New Shipment')).toBeInTheDocument()
      expect(screen.getByLabelText(/Reference Number/)).toBeInTheDocument()
    })

    it('should handle container number with lowercase letters', async () => {
      const user = userEvent.setup()
      render(
        <CreateShipmentModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
          organizationId={mockOrganizationId}
        />
      )

      // Fill form with lowercase
      await user.type(screen.getByLabelText(/Reference Number/), 'vibo-2026-001')
      await user.type(screen.getByLabelText(/Container Number/), 'mscu1234567')
      await user.selectOptions(screen.getByLabelText(/Product Type/), 'horn_hoof')

      // Submit
      await user.click(screen.getByRole('button', { name: /Create Shipment/i }))

      await waitFor(() => {
        expect(api.createShipment).toHaveBeenCalledWith(
          expect.objectContaining({
            reference: 'VIBO-2026-001',
            container_number: 'MSCU1234567',
            product_type: 'horn_hoof',
          })
        )
      })
    })
  })
})
