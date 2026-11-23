/** Başlıkta ".pdf" uzantısını göstermeye gerek yok; PDF rozeti zaten var. */
export function displayTitle(title: string): string {
  return title.replace(/\.pdf$/i, "");
}
