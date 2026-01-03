import { Ship, Package, MapPin, Anchor, Truck, Clock } from 'lucide-react'
import type { ContainerEvent, EventType } from '../types'
import { format, formatDistanceToNow } from 'date-fns'

interface TrackingTimelineProps {
  events: ContainerEvent[]
  currentStatus?: string
}

const EVENT_CONFIG: Record<EventType, { icon: typeof Ship; color: string; label: string }> = {
  booking_confirmed: { icon: Clock, color: 'bg-gray-100 text-gray-600', label: 'Booking Confirmed' },
  gate_in: { icon: Package, color: 'bg-blue-100 text-blue-600', label: 'Gate In' },
  loaded: { icon: Ship, color: 'bg-primary-100 text-primary-600', label: 'Loaded on Vessel' },
  departed: { icon: Ship, color: 'bg-primary-100 text-primary-600', label: 'Departed' },
  transshipment: { icon: Anchor, color: 'bg-warning-100 text-warning-600', label: 'Transshipment' },
  arrived: { icon: Anchor, color: 'bg-success-100 text-success-600', label: 'Arrived' },
  discharged: { icon: Package, color: 'bg-success-100 text-success-600', label: 'Discharged' },
  gate_out: { icon: Truck, color: 'bg-success-100 text-success-600', label: 'Gate Out' },
  delivered: { icon: MapPin, color: 'bg-success-100 text-success-600', label: 'Delivered' },
  customs_hold: { icon: Clock, color: 'bg-danger-100 text-danger-600', label: 'Customs Hold' },
  customs_released: { icon: Clock, color: 'bg-success-100 text-success-600', label: 'Customs Released' },
  empty_return: { icon: Package, color: 'bg-gray-100 text-gray-600', label: 'Empty Container Returned' },
  unknown: { icon: Clock, color: 'bg-gray-100 text-gray-600', label: 'Unknown Event' },
}

export default function TrackingTimeline({ events, currentStatus }: TrackingTimelineProps) {
  // Sort events by timestamp (most recent first)
  const sortedEvents = [...events].sort(
    (a, b) => new Date(b.event_timestamp).getTime() - new Date(a.event_timestamp).getTime()
  )

  if (events.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Ship className="h-8 w-8 mx-auto mb-2 text-gray-400" />
        <p>No tracking events yet</p>
      </div>
    )
  }

  return (
    <div className="flow-root">
      <ul className="-mb-8">
        {sortedEvents.map((event, idx) => {
          const config = EVENT_CONFIG[event.event_type] || {
            icon: Clock,
            color: 'bg-gray-100 text-gray-600',
            label: event.event_type,
          }
          const Icon = config.icon
          const isLatest = idx === 0

          return (
            <li key={event.id}>
              <div className="relative pb-8">
                {/* Connector line */}
                {idx !== sortedEvents.length - 1 && (
                  <span
                    className="absolute left-5 top-10 -ml-px h-full w-0.5 bg-gray-200"
                    aria-hidden="true"
                  />
                )}

                <div className="relative flex items-start space-x-4">
                  {/* Icon */}
                  <div className={`relative flex h-10 w-10 items-center justify-center rounded-full ${config.color} ${isLatest ? 'ring-2 ring-primary-500 ring-offset-2' : ''}`}>
                    <Icon className="h-5 w-5" />
                  </div>

                  {/* Content */}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between">
                      <p className={`text-sm font-medium ${isLatest ? 'text-gray-900' : 'text-gray-700'}`}>
                        {config.label}
                        {isLatest && (
                          <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary-100 text-primary-700">
                            Latest
                          </span>
                        )}
                      </p>
                      <time className="text-xs text-gray-500">
                        {formatDistanceToNow(new Date(event.event_timestamp), { addSuffix: true })}
                      </time>
                    </div>

                    <div className="mt-1 text-sm text-gray-600">
                      <div className="flex items-center">
                        <MapPin className="h-3 w-3 mr-1 text-gray-400" />
                        <span>{event.location_name || 'Location unknown'}</span>
                        {event.location_code && (
                          <span className="ml-1 text-gray-400">({event.location_code})</span>
                        )}
                      </div>

                      {event.vessel_name && (
                        <div className="flex items-center mt-1">
                          <Ship className="h-3 w-3 mr-1 text-gray-400" />
                          <span>
                            {event.vessel_name}
                            {event.voyage_number && ` / ${event.voyage_number}`}
                          </span>
                        </div>
                      )}

                      <p className="text-xs text-gray-400 mt-1">
                        {format(new Date(event.event_timestamp), 'PPpp')}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
