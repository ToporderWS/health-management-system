/* 从 npmmirror 下载 uCharts 官方包并解出 u-charts.js（uni-app 非 npm 工程手动引入方式）
   运行方式：node tools/fetch_ucharts.js
   输出：miniapp/components/u-charts/u-charts.js
 */
const https = require('https')
const http = require('http')
const fs = require('fs')
const path = require('path')
const zlib = require('zlib')

const URL_ = 'https://registry.npmmirror.com/@qiun/ucharts/-/ucharts-2.5.0-20230101.tgz'
const ROOT = path.join(__dirname, '..')
const OUT = path.join(ROOT, '_ucharts.tgz')

function download(url, depth = 0) {
  return new Promise((resolve, reject) => {
    if (depth > 5) return reject(new Error('too many redirects'))
    const mod = url.startsWith('https') ? https : http
    mod.get(url, { timeout: 60000 }, (res) => {
      if ([301, 302, 303, 307, 308].includes(res.statusCode) && res.headers.location) {
        res.resume()
        resolve(download(new URL(res.headers.location, url).href, depth + 1))
        return
      }
      if (res.statusCode !== 200) return reject(new Error('HTTP ' + res.statusCode))
      const f = fs.createWriteStream(OUT)
      res.pipe(f)
      f.on('finish', () => f.close(() => resolve(OUT)))
      f.on('error', reject)
    }).on('error', reject)
  })
}

/* 极简 tar 解析：仅取普通文件 */
function untar(buf) {
  const files = {}
  let off = 0
  while (off + 512 <= buf.length) {
    const header = buf.subarray(off, off + 512)
    const name = header.subarray(0, 100).toString('utf8').replace(/\0.*$/, '')
    if (!name) break
    const sizeStr = header.subarray(124, 136).toString('utf8').replace(/\0.*$/, '').trim()
    const size = parseInt(sizeStr, 8) || 0
    const type = String.fromCharCode(header[156])
    const dataStart = off + 512
    if (type === '0' || type === '\0' || type === '') {
      files[name] = buf.subarray(dataStart, dataStart + size)
    }
    off = dataStart + Math.ceil(size / 512) * 512
  }
  return files
}

;(async () => {
  await download(URL_)
  const raw = fs.readFileSync(OUT)
  const gz = zlib.gunzipSync(raw)
  const files = untar(gz)
  console.log('tarball entries:', Object.keys(files).join(' | '))

  const target = Object.keys(files).find((n) => /(^|\/)u-charts(\.min)?\.js$/.test(n))
  if (!target) {
    console.log('FAIL: 未在包中找到 u-charts.js')
    process.exit(1)
  }
  const dest = path.join(ROOT, 'miniapp', 'components', 'u-charts', 'u-charts.js')
  fs.mkdirSync(path.dirname(dest), { recursive: true })
  fs.writeFileSync(dest, files[target])
  console.log('OK ->', dest, fs.statSync(dest).size, 'bytes  (from', target + ')')
  fs.unlinkSync(OUT)
})()
