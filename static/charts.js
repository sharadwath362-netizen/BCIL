const body = document.body;

function getTextColor() {
    return body.classList.contains("light-mode") ? "#111827" : "#e5e7eb";
}

function createCharts(itemNames, quantities, dates, dailyCounts) {
    const textColor = getTextColor();
    const maxQty = Math.max(...quantities, 1);
    const stockColors = quantities.map(q => q/maxQty<0.3?"#ef4444":q/maxQty<0.6?"#facc15":"#22c55e");

    window.popularityChart = new Chart(document.getElementById("popularityChart"), {
        type: "bar",
        data: { labels: itemNames, datasets: [{ label: "Quantity", data: quantities, backgroundColor: "#60a5fa" }] },
        options: {
            indexAxis: "y",
            responsive: true,
            plugins: { legend: { display: false, labels: { color: textColor } } },
            scales: { x: { ticks: { color: textColor } }, y: { ticks: { color: textColor } } }
        }
    });

    window.stockChart = new Chart(document.getElementById("stockChart"), {
        type: "bar",
        data: { labels: itemNames, datasets: [{ label: "Stock Level", data: quantities, backgroundColor: stockColors }] },
        options: {
            responsive: true,
            plugins: { legend: { display: false, labels: { color: textColor } } },
            scales: { x: { ticks: { color: textColor } }, y: { ticks: { color: textColor } } }
        }
    });

    window.dailyActivityChart = new Chart(document.getElementById("dailyActivityChart"), {
        type: "line",
        data: {
            labels: dates,
            datasets: [{
                label: "Daily Activity",
                data: dailyCounts,
                borderColor: "#3b82f6",
                backgroundColor: "rgba(59,130,246,0.2)",
                fill: true,
                tension: 0.3,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: textColor } } },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: "Items Added/Removed", color: textColor }, ticks: { color: textColor } },
                x: { title: { display: true, text: "Date", color: textColor }, ticks: { color: textColor } }
            }
        }
    });
}

function updateChartColors() {
    const textColor = getTextColor();
    [window.popularityChart, window.stockChart, window.dailyActivityChart].forEach(chart => {
        chart.options.scales.x.ticks.color = textColor;
        chart.options.scales.y.ticks.color = textColor;
        if(chart.options.scales.x.title) chart.options.scales.x.title.color = textColor;
        if(chart.options.scales.y.title) chart.options.scales.y.title.color = textColor;
        if(chart.options.plugins.legend.labels) chart.options.plugins.legend.labels.color = textColor;
        chart.update();
    });
}
