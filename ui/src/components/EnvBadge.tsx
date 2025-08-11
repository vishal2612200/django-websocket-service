import React from 'react'
import Box from '@mui/material/Box'

export default function EnvBadge({ color }: { color: string }) {
  const tone = String(color || 'unknown').toLowerCase()
  const bg = tone === 'blue' ? 'rgba(78,168,255,.2)' : tone === 'green' ? 'rgba(61,220,151,.2)' : 'rgba(159,176,200,.1)'
  const dot = tone === 'blue' ? '#4ea8ff' : tone === 'green' ? '#3ddc97' : '#9fb0c8'
  const label = (tone || 'unknown').toUpperCase()
  return (
    <Box title={'Tip: Flip environments with "make promote".'} sx={{ display: 'inline-flex', alignItems: 'center', gap: 1, px: 1.25, py: .5, borderRadius: 999, border: '1px solid', borderColor: 'divider', bgcolor: bg, fontWeight: 600 }}>
      <Box sx={{ width: 10, height: 10, borderRadius: '999px', bgcolor: dot }} />
      <Box component="span" sx={{ whiteSpace: 'nowrap', maxWidth: 160, textOverflow: 'ellipsis', overflow: 'hidden' }}>{label}</Box>
    </Box>
  )
}


