import React from 'react'

// ==========================================
// 1. FACEBOOK
// ==========================================
export const FacebookIcon: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
  </svg>
)

export const FacebookBadge: React.FC<{ className?: string; size?: 'sm' | 'md' | 'lg' }> = ({
  className = '',
  size = 'md',
}) => {
  const sizeClass = size === 'sm' ? 'w-6 h-6' : size === 'lg' ? 'w-12 h-12' : 'w-10 h-10'
  const iconSize = size === 'sm' ? 'w-3.5 h-3.5' : size === 'lg' ? 'w-7 h-7' : 'w-5 h-5'
  return (
    <div
      className={`${sizeClass} rounded-xl bg-[#1877F2] text-white flex items-center justify-center shadow-sm shadow-blue-500/20 shrink-0 ${className}`}
    >
      <FacebookIcon className={iconSize} />
    </div>
  )
}

// ==========================================
// 2. MESSENGER
// ==========================================
export const MessengerIcon: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M12 0C5.373 0 0 4.974 0 11.111c0 3.498 1.744 6.614 4.469 8.654V24l4.088-2.242c1.085.3 2.235.464 3.443.464 6.627 0 12-4.975 12-11.111C24 4.974 18.627 0 12 0zm1.191 14.963l-3.055-3.26-5.963 3.26 6.559-6.962 3.131 3.259 5.887-3.259-6.559 6.962z" />
  </svg>
)

export const MessengerBadge: React.FC<{ className?: string; size?: 'sm' | 'md' | 'lg' }> = ({
  className = '',
  size = 'md',
}) => {
  const sizeClass = size === 'sm' ? 'w-6 h-6' : size === 'lg' ? 'w-12 h-12' : 'w-10 h-10'
  const iconSize = size === 'sm' ? 'w-3.5 h-3.5' : size === 'lg' ? 'w-7 h-7' : 'w-5 h-5'
  return (
    <div
      className={`${sizeClass} rounded-xl bg-gradient-to-tr from-[#006AFF] via-[#00B2FF] to-[#00E5FF] text-white flex items-center justify-center shadow-sm shadow-cyan-500/20 shrink-0 ${className}`}
    >
      <MessengerIcon className={iconSize} />
    </div>
  )
}

// ==========================================
// 3. TIKTOK
// ==========================================
export const TikTokIcon: React.FC<{ className?: string; colored?: boolean }> = ({
  className = 'w-5 h-5',
  colored = false,
}) => {
  if (colored) {
    return (
      <svg viewBox="0 0 24 24" className={className}>
        {/* TikTok Authentic 3D Multi-color layers */}
        <path
          d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64c.29 0 .58.04.85.12V9.4a6.33 6.33 0 0 0-1-.08A6.34 6.34 0 0 0 3 15.66a6.34 6.34 0 0 0 10.82 4.46 6.27 6.27 0 0 0 1.9-4.46V8.65a8.28 8.28 0 0 0 4.87 1.57V6.78a4.85 4.85 0 0 1-1-.09z"
          fill="#25F4EE"
          transform="translate(-0.8, -0.6)"
        />
        <path
          d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64c.29 0 .58.04.85.12V9.4a6.33 6.33 0 0 0-1-.08A6.34 6.34 0 0 0 3 15.66a6.34 6.34 0 0 0 10.82 4.46 6.27 6.27 0 0 0 1.9-4.46V8.65a8.28 8.28 0 0 0 4.87 1.57V6.78a4.85 4.85 0 0 1-1-.09z"
          fill="#FE2C55"
          transform="translate(0.8, 0.6)"
        />
        <path
          d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64c.29 0 .58.04.85.12V9.4a6.33 6.33 0 0 0-1-.08A6.34 6.34 0 0 0 3 15.66a6.34 6.34 0 0 0 10.82 4.46 6.27 6.27 0 0 0 1.9-4.46V8.65a8.28 8.28 0 0 0 4.87 1.57V6.78a4.85 4.85 0 0 1-1-.09z"
          fill="#FFFFFF"
        />
      </svg>
    )
  }
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64c.29 0 .58.04.85.12V9.4a6.33 6.33 0 0 0-1-.08A6.34 6.34 0 0 0 3 15.66a6.34 6.34 0 0 0 10.82 4.46 6.27 6.27 0 0 0 1.9-4.46V8.65a8.28 8.28 0 0 0 4.87 1.57V6.78a4.85 4.85 0 0 1-1-.09z" />
    </svg>
  )
}

export const TikTokBadge: React.FC<{ className?: string; size?: 'sm' | 'md' | 'lg' }> = ({
  className = '',
  size = 'md',
}) => {
  const sizeClass = size === 'sm' ? 'w-6 h-6' : size === 'lg' ? 'w-12 h-12' : 'w-10 h-10'
  const iconSize = size === 'sm' ? 'w-3.5 h-3.5' : size === 'lg' ? 'w-7 h-7' : 'w-5 h-5'
  return (
    <div
      className={`${sizeClass} rounded-xl bg-[#010101] text-white flex items-center justify-center shadow-sm shadow-slate-900/30 shrink-0 border border-slate-800 ${className}`}
    >
      <TikTokIcon className={iconSize} colored={true} />
    </div>
  )
}

// ==========================================
// 4. INSTAGRAM
// ==========================================
export const InstagramIcon: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
  </svg>
)

export const InstagramBadge: React.FC<{ className?: string; size?: 'sm' | 'md' | 'lg' }> = ({
  className = '',
  size = 'md',
}) => {
  const sizeClass = size === 'sm' ? 'w-6 h-6' : size === 'lg' ? 'w-12 h-12' : 'w-10 h-10'
  const iconSize = size === 'sm' ? 'w-3.5 h-3.5' : size === 'lg' ? 'w-7 h-7' : 'w-5 h-5'
  return (
    <div
      className={`${sizeClass} rounded-xl bg-gradient-to-tr from-[#FFB900] via-[#E60064] to-[#7900C4] text-white flex items-center justify-center shadow-sm shadow-rose-500/20 shrink-0 ${className}`}
    >
      <InstagramIcon className={iconSize} />
    </div>
  )
}

// ==========================================
// 5. YOUTUBE
// ==========================================
export const YouTubeIcon: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
  </svg>
)

export const YouTubeBadge: React.FC<{ className?: string; size?: 'sm' | 'md' | 'lg' }> = ({
  className = '',
  size = 'md',
}) => {
  const sizeClass = size === 'sm' ? 'w-6 h-6' : size === 'lg' ? 'w-12 h-12' : 'w-10 h-10'
  const iconSize = size === 'sm' ? 'w-3.5 h-3.5' : size === 'lg' ? 'w-7 h-7' : 'w-5 h-5'
  return (
    <div
      className={`${sizeClass} rounded-xl bg-[#FF0000] text-white flex items-center justify-center shadow-sm shadow-red-500/20 shrink-0 ${className}`}
    >
      <YouTubeIcon className={iconSize} />
    </div>
  )
}

// ==========================================
// 6. THREADS
// ==========================================
export const ThreadsIcon: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M12.186 24C5.46 24 0 18.541 0 11.815 0 5.089 5.46-.369 12.186-.369c6.643 0 11.968 5.257 12.046 11.9.08 6.776-5.32 12.469-12.046 12.469zm-.046-2.164c5.443 0 9.878-4.57 9.805-10.08-.073-5.512-4.38-9.837-9.805-9.837-5.46 0-9.92 4.46-9.92 9.92 0 5.46 4.46 9.997 9.92 9.997zm6.002-9.997c0 3.315-2.686 6-6.002 6s-6.002-2.685-6.002-6 2.686-6 6.002-6c1.558 0 2.973.593 4.043 1.564l-1.506 1.506c-.673-.61-1.562-.98-2.537-.98-2.155 0-3.91 1.755-3.91 3.91s1.755 3.91 3.91 3.91c1.99 0 3.633-1.493 3.876-3.432H12.14v-2.09h5.972c.046.33.076.67.076 1.012z" />
  </svg>
)

export const ThreadsBadge: React.FC<{ className?: string; size?: 'sm' | 'md' | 'lg' }> = ({
  className = '',
  size = 'md',
}) => {
  const sizeClass = size === 'sm' ? 'w-6 h-6' : size === 'lg' ? 'w-12 h-12' : 'w-10 h-10'
  const iconSize = size === 'sm' ? 'w-3.5 h-3.5' : size === 'lg' ? 'w-7 h-7' : 'w-5 h-5'
  return (
    <div
      className={`${sizeClass} rounded-xl bg-black text-white flex items-center justify-center shadow-sm shrink-0 border border-slate-800 ${className}`}
    >
      <ThreadsIcon className={iconSize} />
    </div>
  )
}

// ==========================================
// 7. X (TWITTER)
// ==========================================
export const XTwitterIcon: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
  </svg>
)

// ==========================================
// 8. LINKEDIN
// ==========================================
export const LinkedInIcon: React.FC<{ className?: string }> = ({ className = 'w-5 h-5' }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
  </svg>
)

// ==========================================
// UNIVERSAL PLATFORM BADGE COMPONENT
// ==========================================
export type PlatformType =
  | 'facebook'
  | 'messenger'
  | 'tiktok'
  | 'instagram'
  | 'youtube'
  | 'threads'
  | 'website'
  | string

export const PlatformBadge: React.FC<{
  platform: PlatformType
  size?: 'sm' | 'md' | 'lg'
  className?: string
}> = ({ platform, size = 'md', className = '' }) => {
  const norm = platform.toLowerCase()
  if (norm.includes('facebook') || norm === 'fb') {
    return <FacebookBadge size={size} className={className} />
  }
  if (norm.includes('messenger')) {
    return <MessengerBadge size={size} className={className} />
  }
  if (norm.includes('tiktok')) {
    return <TikTokBadge size={size} className={className} />
  }
  if (norm.includes('instagram') || norm === 'ig') {
    return <InstagramBadge size={size} className={className} />
  }
  if (norm.includes('youtube') || norm === 'yt') {
    return <YouTubeBadge size={size} className={className} />
  }
  if (norm.includes('thread')) {
    return <ThreadsBadge size={size} className={className} />
  }

  // Fallback web / generic
  const sizeClass = size === 'sm' ? 'w-6 h-6' : size === 'lg' ? 'w-12 h-12' : 'w-10 h-10'
  return (
    <div
      className={`${sizeClass} rounded-xl bg-slate-100 text-slate-600 flex items-center justify-center font-bold text-xs shrink-0 ${className}`}
    >
      🌐
    </div>
  )
}

// ==========================================
// UNIVERSAL PLATFORM PILL / TAG (For Tables)
// ==========================================
export const PlatformPill: React.FC<{ platform: PlatformType; className?: string }> = ({
  platform,
  className = '',
}) => {
  const norm = platform.toLowerCase()
  if (norm.includes('facebook') || norm === 'fb') {
    return (
      <span
        className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200/80 shadow-2xs ${className}`}
      >
        <FacebookIcon className="w-3.5 h-3.5 text-[#1877F2]" />
        <span>Facebook</span>
      </span>
    )
  }
  if (norm.includes('messenger')) {
    return (
      <span
        className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-cyan-50 text-cyan-700 border border-cyan-200/80 shadow-2xs ${className}`}
      >
        <MessengerIcon className="w-3.5 h-3.5 text-[#0084FF]" />
        <span>Messenger</span>
      </span>
    )
  }
  if (norm.includes('tiktok')) {
    return (
      <span
        className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-900 text-white shadow-2xs ${className}`}
      >
        <TikTokIcon className="w-3.5 h-3.5" colored={true} />
        <span>TikTok</span>
      </span>
    )
  }
  if (norm.includes('instagram') || norm === 'ig') {
    return (
      <span
        className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200/80 shadow-2xs ${className}`}
      >
        <InstagramIcon className="w-3.5 h-3.5 text-[#E60064]" />
        <span>Instagram</span>
      </span>
    )
  }
  if (norm.includes('youtube') || norm === 'yt') {
    return (
      <span
        className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-red-50 text-red-700 border border-red-200/80 shadow-2xs ${className}`}
      >
        <YouTubeIcon className="w-3.5 h-3.5 text-[#FF0000]" />
        <span>YouTube</span>
      </span>
    )
  }
  if (norm.includes('thread')) {
    return (
      <span
        className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-100 text-slate-800 border border-slate-200 shadow-2xs ${className}`}
      >
        <ThreadsIcon className="w-3.5 h-3.5 text-black" />
        <span>Threads</span>
      </span>
    )
  }

  return (
    <span
      className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-100 text-slate-700 ${className}`}
    >
      <span>🌐</span>
      <span>Website</span>
    </span>
  )
}
