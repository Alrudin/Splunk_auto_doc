interface StatusBadgeProps {
  status: string
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const statusLower = status.toLowerCase()

  let colorClasses = 'bg-gray-100 text-gray-800'
  if (statusLower === 'completed' || statusLower === 'complete') {
    colorClasses = 'bg-green-100 text-green-800'
  } else if (statusLower === 'pending' || statusLower === 'processing') {
    colorClasses = 'bg-yellow-100 text-yellow-800'
  } else if (statusLower === 'failed' || statusLower === 'error') {
    colorClasses = 'bg-red-100 text-red-800'
  } else if (statusLower === 'parsing' || statusLower === 'normalized') {
    colorClasses = 'bg-blue-100 text-blue-800'
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClasses}`}
    >
      {status}
    </span>
  )
}
