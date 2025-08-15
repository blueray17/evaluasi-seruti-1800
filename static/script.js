let chartInstance = null;
let judul = null;
var count = 0;
Chart.register(ChartDataLabels);

async function runQuery(queryId,buttonElement) {
  //kosongkan area kanan
  document.getElementById("hasil").innerHTML = "";
  document.getElementById("deskripsi").innerHTML = "";
  document.getElementById("loading-gif").innerHTML = "<img src='static/loading_2.gif' width='20' height='20'>";
  document.getElementById("count").innerHTML = "";
  
  const res1 = await fetch(`/get-query/${queryId}`);
  const query = await res1.json();

  //ambil parameter
  const kode_prov = document.getElementById("kd_prov").value;
  const kode_kab = document.getElementById("kd_kab").value;
  const trw = document.getElementById("tw").value;

  const res2 = await fetch("/proxy-seruti", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      kd_prov:kode_prov,
      kd_kab:kode_kab,
      tw:trw,
      raw: query.raw,
      limit: query.limit
    })
  });

  //blur
  //document.getElementById("overlay").style.display = "block";

  //tampilin deskripsi
  const parentDiv = buttonElement.parentElement;
  const paragraph = parentDiv.querySelector("p");
  if (paragraph) document.getElementById("deskripsi").innerText = paragraph.innerText;
  judul = buttonElement.innerText;
  document.getElementById("loading-gif").innerHTML = "";
  //console.log(judul)

  const data = await res2.json();
  document.getElementById("hasil").innerHTML = "";
  //console.log(data.message);
  if(data.message=="CSRF token mismatch."){
    alert("Token expired, silahkan perbaharui lagi");
    return;
  }else if(data.error = ""){
    alert("Cek Token atau parameter");
    return;
  }else if(typeof data.data == 'undefined'){
    alert("Data tidak tersedia, silahkan pilih parameter lain");
    document.getElementById("result-chart").style.display = "none";
    document.getElementById("hasil").innerHTML = "";
    document.getElementById("deskripsi").innerHTML = "";
    return;
  }

  if (query.tipe === "tabel") {
    document.getElementById("result-chart").style.display = "none";
    document.getElementById("result-chart").innerHTML = "";
    document.getElementById("hasil").innerHTML = renderTable(data);
    document.getElementById("count").innerHTML = "Total : "+count+" baris";
  } else if (query.tipe === "grafik") {
    const labelKey = Object.keys(data.data[0])[0];
    const valueKey = Object.keys(data.data[0])[1];

    const labels = data.data.map(row => row[labelKey]);
    const values = data.data.map(row => parseInt(row[valueKey], 10));

    //console.log("Labels:", labels);
    //console.log("Values:", values);

    document.getElementById("result-chart").style.display = "block";
    renderChart(labels, values);
  }
  
}

function renderTable(data) {
  if (!data.data || !data.data.length) return "Tidak ada data.";
  const keys = Object.keys(data.data[0]);
  count = data.data.length;
  let html = "<table><thead><tr>";
  for (const key of keys) html += `<th>${key}</th>`;
  html += "</tr></thead><tbody>";
  for (const row of data.data) {
    html += "<tr>";
    for (const key of keys) html += `<td>${row[key]}</td>`;
    html += "</tr>";
  }
  html += "</tbody></table>";
  return html;
}

function renderChart(labels, values) {
//  console.log("judul = "+judul)
  const ctx = document.getElementById("result-chart").getContext("2d");

  if (window.resultChart) {
    window.resultChart.destroy();
  }

  window.resultChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Frekuensi",
        data: values,
        backgroundColor: "rgba(75, 192, 192, 0.5)",
        borderColor: "rgba(75, 192, 192, 1)",
        borderWidth: 3
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: judul
        },
        datalabels: {
          anchor: 'end',
          align: 'top',
          formatter: function(value) {
            return value.toLocaleString('id-ID');
          },
          font: {
            size: 14,
            weight: 'bold'
          },
          color: '#000'
        },
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              return context.raw.toLocaleString('id-ID');
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return value.toLocaleString('id-ID');
            }
          }
        }
      }
    },
    plugins: [ChartDataLabels]
  });
}
