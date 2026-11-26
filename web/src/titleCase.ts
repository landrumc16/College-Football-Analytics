/** Title Case for interface labels only. Never apply to prose, IDs or source data. */
const minorWords = new Set('a an the and but or nor for so yet as at by in of on per to up via vs with from into onto over off out than upon within without'.split(' '))
const acronyms = new Set('CFA AP CFP FBS FCS PWA EPA PPD SR SOS FPI FEI SP SD SE ATS MAE MSE RMSE BCS NFL NCAA QB QBR ACC SEC AAC MAC CUSA MWC PAC BIG O U N A I II III IV V VI VII VIII IX X ND P4 G5 G6 NIL API JSON CSV UI URL UTC ISO SP+ BYU TCU SMU LSU UCF UCLA USC UTEP UTSA UNLV FIU FAU USF UAB ULM ULL SJSU NMSU FL OH AL AK AZ AR CA CO CT DE GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split(' '))
export function titleCase(text: string, first = true, last = true): string {
  const words = [...text.matchAll(/[\p{L}][\p{L}\p{N}'’+]*/gu)]
  let index = 0
  return text.replace(/[\p{L}][\p{L}\p{N}'’+]*/gu, (word, offset: number) => {
    const current = index++
    if (text[offset - 1] === '&' && text[offset + word.length] === ';') return word
    if (text.slice(Math.max(0, offset - 4), offset + word.length).endsWith('EPA/play')) return word
    const base = word.replace(/['’]s$/i, '')
    if (acronyms.has(base.toUpperCase()) && (word === word.toUpperCase() || acronyms.has(base))) return word
    // Keep established mixed-case names, e.g. McNeese, UConn and OpenAI.
    if (/[a-z].*[A-Z]|^[A-Z]{2,}[a-z]/.test(word)) return word
    const lower = word.toLowerCase()
    // Over/Under is a named market metric, rather than the preposition 'over'.
    if (lower === 'over' && text.slice(offset, offset + 10).toLowerCase() === 'over/under') return 'Over'
    const boundary = (current === 0 && first) || (current === words.length - 1 && last) || /[:—–]\s*$/.test(text.slice(0, offset))
    return !boundary && minorWords.has(lower) ? lower : lower[0].toUpperCase() + lower.slice(1)
  })
}
