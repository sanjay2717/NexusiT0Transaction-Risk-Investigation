document.addEventListener("DOMContentLoaded", () => {
    fetch('/api/customers')
        .then(res => res.json())
        .then(data => {
            const list = document.getElementById('customer-list');
            list.innerHTML = '';
            data.forEach(cust => {
                const btn = document.createElement('button');
                btn.className = 'customer-btn';
                btn.textContent = cust.name;
                btn.onclick = () => loadReport(cust.id, cust.name);
                list.appendChild(btn);
            });
        });
});

function loadReport(custId, custName) {
    document.getElementById('report-title').textContent = `Report for ${custName}`;
    document.getElementById('report-content').style.display = 'none';
    document.getElementById('loading').style.display = 'block';
    
    fetch(`/api/customers/${custId}/report`)
        .then(res => {
            if (!res.ok) throw new Error("Failed to load report");
            return res.json();
        })
        .then(data => {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('report-content').style.display = 'block';
            document.getElementById('verdict').textContent = data.verdict;
            document.getElementById('narrative').textContent = data.narrative;
        })
        .catch(err => {
            document.getElementById('loading').style.display = 'none';
            alert(err.message);
        });
}
