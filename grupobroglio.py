$(document).ready(function () {
    let dataTable;
    let allMonths = []; // Tornando `allMonths` global para ser usada na exportação

    // Função para ler o arquivo Excel
    document.getElementById('fileUpload').addEventListener('change', function (event) {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = function (e) {
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, { type: 'array' });
            const firstSheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[firstSheetName];
            const jsonData = XLSX.utils.sheet_to_json(worksheet, { defval: "" });

            if (jsonData.length === 0) {
                alert("O arquivo está vazio ou não possui dados válidos.");
                return;
            }

            populateDataTable(jsonData);
            populateStoreFilter(jsonData);
            calculateSummary(jsonData);
            updateCards(jsonData); // Atualiza os cards de resumo
        };
        reader.readAsArrayBuffer(file);
    });

    // Função para popular a tabela com DataTables
    function populateDataTable(data) {
        if (dataTable) {
            dataTable.clear().destroy();
        }

        const tableBody = $('#excelTable tbody');
        tableBody.empty();

        data.forEach(row => {
            const { Descrição, "Plano de contas": planoDeContas, "Conta bancária": contaBancaria, Loja, Data, Valor } = row;

            // Tratamento e formatação da data no formato brasileiro (dd/mm/yyyy)
            const formattedData = parseDateBR(Data);
            const formattedValor = isNaN(parseFloat(Valor.toString().replace(',', '.'))) ? '0.00' : parseFloat(Valor.toString().replace(',', '.')).toFixed(2);

            const formattedRow = `
                <tr>
                    <td>${Descrição}</td>
                    <td>${planoDeContas}</td>
                    <td>${contaBancaria}</td>
                    <td>${Loja}</td>
                    <td>${formattedData}</td>
                    <td>${formattedValor}</td>
                </tr>
            `;
            tableBody.append(formattedRow);
        });

        dataTable = $('#excelTable').DataTable({
            responsive: true,
            language: {
                decimal: ",",
                thousands: ".",
                emptyTable: "Nenhum dado disponível na tabela",
                info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                infoEmpty: "Mostrando 0 a 0 de 0 entradas",
                infoFiltered: "(filtrado de _MAX_ entradas totais)",
                lengthMenu: "Mostrar _MENU_ entradas",
                loadingRecords: "Carregando...",
                processing: "Processando...",
                search: "Buscar:",
                zeroRecords: "Nenhum registro correspondente encontrado",
                paginate: {
                    first: "Primeiro",
                    last: "Último",
                    next: "Próximo",
                    previous: "Anterior"
                }
            }
        });

        // Reaplica o filtro de loja se um estiver selecionado
        $('#filterStore').trigger('change');
    }

    // Função para popular o filtro de lojas
    function populateStoreFilter(data) {
        const storeSet = new Set();
        data.forEach(row => {
            if (row.Loja) {
                storeSet.add(row.Loja.trim());
            }
        });

        const filterStore = $('#filterStore');
        filterStore.empty();
        filterStore.append('<option value="">Todas as Lojas</option>');
        storeSet.forEach(store => {
            filterStore.append(`<option value="${store}">${store}</option>`);
        });

        // Event listener para filtrar a tabela quando o valor do filtro for alterado
        filterStore.off('change').on('change', function () {
            const selectedStore = $(this).val().toLowerCase();
            if (dataTable) {
                dataTable.column(3).search(selectedStore, false, false).draw();
            }
            calculateSummary(getFilteredData());
            updateCards(getFilteredData()); // Atualiza os cards conforme o filtro
        });
    }

    // Função para obter os dados filtrados pela loja
    function getFilteredData() {
        return dataTable.rows({ filter: 'applied' }).data().toArray().map(row => ({
            "Descrição": row[0],
            "Plano de contas": row[1],
            "Conta bancária": row[2],
            "Loja": row[3],
            "Data": row[4],
            "Valor": row[5]
        }));
    }

    // Função para calcular e mostrar o resumo por "Plano de Contas" agrupado por Mês/Ano
    function calculateSummary(data) {
        const summary = {};
        const positiveValuesByCategory = {};
        const negativeValuesByCategory = {};

        // Organizando os dados por Plano de Contas e Mês/Ano
        data.forEach(row => {
            const planoDeContas = row["Plano de contas"]?.trim();
            const valor = parseFloat(row["Valor"].toString().replace(',', '.')) || 0;
            const mesAno = parseMonthYearBR(row["Data"]);

            // Somando valores positivos por categoria para o gráfico de entradas de disponibilidade
            if (mesAno && valor > 0) {
                if (!positiveValuesByCategory[planoDeContas]) {
                    positiveValuesByCategory[planoDeContas] = {};
                }
                if (!positiveValuesByCategory[planoDeContas][mesAno]) {
                    positiveValuesByCategory[planoDeContas][mesAno] = 0;
                }
                positiveValuesByCategory[planoDeContas][mesAno] += valor;
            }

            // Somando valores negativos por categoria para o Top 5
            if (mesAno && valor < 0) {
                if (!negativeValuesByCategory[planoDeContas]) {
                    negativeValuesByCategory[planoDeContas] = {};
                }
                if (!negativeValuesByCategory[planoDeContas][mesAno]) {
                    negativeValuesByCategory[planoDeContas][mesAno] = 0;
                }
                negativeValuesByCategory[planoDeContas][mesAno] += Math.abs(valor);
            }

            // Populando o resumo por Plano de Contas
            if (mesAno && planoDeContas) {
                if (!summary[planoDeContas]) {
                    summary[planoDeContas] = {};
                }
                if (!summary[planoDeContas][mesAno]) {
                    summary[planoDeContas][mesAno] = 0;
                }
                summary[planoDeContas][mesAno] += valor;
            }
        });

        // Extraindo todas as chaves de Mês/Ano para criar as colunas da tabela e ordená-las
        allMonths = Array.from(new Set(data.map(row => {
            const mesAno = parseMonthYearBR(row["Data"]);
            return mesAno ? mesAno : null;
        }))).filter(month => month !== null).sort((a, b) => {
            const [monthA, yearA] = a.split('/');
            const [monthB, yearB] = b.split('/');
            return new Date(yearA, monthA - 1) - new Date(yearB, monthB - 1);
        });

        // Criando o cabeçalho da tabela
        const headerRow = $('#summaryHeader');
        headerRow.empty();
        headerRow.append('<th>Plano de Contas</th>');
        allMonths.forEach(month => {
            headerRow.append(`<th>${month}</th>`);
        });
        headerRow.append('<th>Total</th>');

        // Criando o corpo da tabela de resumo
        const summaryBody = $('#summaryTable tbody');
        summaryBody.empty();

        Object.keys(summary).forEach(plano => {
            let row = `<tr><td>${plano}</td>`;
            let totalPorPlano = 0;

            allMonths.forEach(month => {
                const valorMes = summary[plano][month] || 0;
                row += `<td>${valorMes.toFixed(2)}</td>`;
                totalPorPlano += valorMes;
            });

            row += `<td>${totalPorPlano.toFixed(2)}</td>`;
            row += '</tr>';
            summaryBody.append(row);
        });

        renderCharts(positiveValuesByCategory, negativeValuesByCategory, allMonths);
    }

    // Função para renderizar os gráficos
    function renderCharts(positiveValuesByCategory, negativeValuesByCategory, allMonths) {
        const ctx1 = document.getElementById('summaryChart').getContext('2d');
        const ctx2 = document.getElementById('top5NegativeChart').getContext('2d');

        // Gráfico de Entrada de Disponibilidade (valores positivos para todas as categorias)
        if (window.chartInstance1) {
            window.chartInstance1.destroy();
        }

        const datasetsPositive = Object.keys(positiveValuesByCategory).map(category => {
            return {
                label: category,
                data: allMonths.map(month => positiveValuesByCategory[category][month] || 0),
                borderWidth: 2,
                fill: false,
                borderColor: getRandomColor()
            };
        });

        window.chartInstance1 = new Chart(ctx1, {
            type: 'line',
            data: {
                labels: allMonths,
                datasets: datasetsPositive
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        // Gráfico Top 5 das Categorias de Valores Negativos
        if (window.chartInstance2) {
            window.chartInstance2.destroy();
        }

        const top5Categories = Object.entries(negativeValuesByCategory)
            .map(([category, values]) => ({
                category,
                total: Object.values(values).reduce((acc, val) => acc + val, 0)
            }))
            .sort((a, b) => b.total - a.total)
            .slice(0, 5)
            .map(item => item.category);

        const datasetsTop5 = top5Categories.map(category => {
            return {
                label: category,
                data: allMonths.map(month => negativeValuesByCategory[category][month] || 0),
                borderWidth: 2,
                fill: false,
                borderColor: getRandomColor()
            };
        });

        window.chartInstance2 = new Chart(ctx2, {
            type: 'line',
            data: {
                labels: allMonths,
                datasets: datasetsTop5
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Função para atualizar os cards "Total Vendas" e "Total Vendas Balcão" com base nos dados filtrados
    function updateCards(data) {
        let totalVendas = 0;
        let totalVendasBalcao = 0;

        data.forEach(row => {
            const planoDeContas = row["Plano de contas"].toLowerCase();
            const valor = parseFloat(row["Valor"].toString().replace(',', '.')) || 0;

            if (planoDeContas.includes('vendas no balcão')) {
                totalVendasBalcao += valor;
            }
            else if (planoDeContas.includes('vendas')) {
                totalVendas += valor;
            }
        });

        $('#totalVendas').text(totalVendas.toFixed(2));
        $('#totalVendasBalcao').text(totalVendasBalcao.toFixed(2));
    }

    // Função para exportar a tabela resumo para Excel
    document.getElementById('exportExcel').addEventListener('click', function () {
        alert("O arquivo será gerado respeitando o filtro atual.");
        populateExportOptions();
    });

    function populateExportOptions() {
        const wb = XLSX.utils.book_new();

        const ws_data = [["Plano de Contas", ...allMonths, "Total"]];

        $('#summaryTable tbody tr').each(function () {
            const row = [];

            $(this).find('td').each(function () {
                let cellValue = $(this).text().trim();
                if (!isNaN(cellValue) && cellValue !== "") {
                    cellValue = parseFloat(cellValue.replace(',', '.'));
                }
                row.push(cellValue);
            });
            ws_data.push(row);
        });

        const ws = XLSX.utils.aoa_to_sheet(ws_data);
        XLSX.utils.book_append_sheet(wb, ws, "Resumo");
        XLSX.writeFile(wb, "Resumo_Plano_De_Contas.xlsx");
    }

    // Função para analisar e formatar uma data no formato brasileiro (dd/mm/yyyy)
    function parseDateBR(dateString) {
        if (!dateString) return "";

        const parts = dateString.split(/[\/\-\.]/);
        if (parts.length === 3) {
            const day = parseInt(parts[0], 10);
            const month = parseInt(parts[1], 10) - 1;
            const year = parseInt(parts[2], 10);

            const dateObj = new Date(year, month, day);
            if (!isNaN(dateObj)) {
                return dateObj.toLocaleDateString("pt-BR");
            }
        }

        return "";
    }

    // Função para obter o mês/ano de uma data em formato "mm/aaaa"
    function parseMonthYearBR(dateString) {
        if (!dateString) return null;

        const parts = dateString.split(/[\/\-\.]/);
        if (parts.length === 3) {
            const day = parseInt(parts[0], 10);
            const month = parseInt(parts[1], 10) - 1;
            const year = parseInt(parts[2], 10);

            const dateObj = new Date(year, month, day);
            if (!isNaN(dateObj)) {
                return `${month + 1}/${year}`;
            }
        }

        return null;
    }

    // Função para gerar uma cor aleatória
function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

// Filtro para a tabela de resumo por "Plano de Contas"
$('#filterAccountSummary').on('keyup', function () {
    const value = $(this).val().toLowerCase();
    $('#summaryTable tbody tr').filter(function () {
        $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
    });
});

// Atualizar cards "Total Vendas" e "Total Vendas Balcão" ao carregar os dados
$(document).ready(function () {
    $('#exportExcel').on('click', function () {
        alert("O arquivo será gerado respeitando o filtro atual.");
        exportSummary();
    });

    // Configurar eventos adicionais necessários
    $('#filterStore').on('change', function () {
        const selectedStore = $(this).val().toLowerCase();
        if (dataTable) {
            dataTable.column(3).search(selectedStore, false, false).draw();
        }
        calculateSummary(getFilteredData());
        updateCards(getFilteredData());
    });
});

function exportSummary() {
    const wb = XLSX.utils.book_new();
    const ws_data = [["Plano de Contas", ...allMonths, "Total"]];

    $('#summaryTable tbody tr').each(function () {
        const row = [];
        $(this).find('td').each(function () {
            let cellValue = $(this).text().trim();
            if (!isNaN(cellValue) && cellValue !== "") {
                cellValue = parseFloat(cellValue.replace(',', '.'));
            }
            row.push(cellValue);
        });
        ws_data.push(row);
    });

    const ws = XLSX.utils.aoa_to_sheet(ws_data);
    XLSX.utils.book_append_sheet(wb, ws, "Resumo");
    XLSX.writeFile(wb, "Resumo_Plano_De_Contas.xlsx");
}

