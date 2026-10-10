/** 文件下载工具（用于 CSV 导出） */

/** 将 blob 响应保存为本地文件 */
export function saveBlobResponse(response, defaultName) {
  const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8' })
  const filename = parseFilename(response.headers?.['content-disposition']) || defaultName
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(link.href)
}

function parseFilename(disposition) {
  if (!disposition) return ''
  const match = /filename\*?=(?:UTF-8'')?["']?([^"';]+)/i.exec(disposition)
  return match ? decodeURIComponent(match[1]) : ''
}

/** 前端本地生成 CSV（带 BOM，Excel 打开不乱码） */
export function exportRowsToCsv(header, rows, filename) {
  const escape = (val) => {
    const text = val === null || val === undefined ? '' : String(val)
    return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
  }
  const lines = [header.map(escape).join(',')]
  rows.forEach((row) => lines.push(row.map(escape).join(',')))
  const blob = new Blob(['\ufeff' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(link.href)
}
