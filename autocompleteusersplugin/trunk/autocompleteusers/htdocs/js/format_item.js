function formatItem(row) {
  var firstLine = (row[2]) ? row[0] + " (" + row[2] + ")" : row[0];
  return $.htmlFormat('<div class="name">$1</div>', firstLine) +
    (row[1] ? $.htmlFormat('<div class="mail">$1</div>', row[1]) : '');
}
