$('#services').on('change', function () {
        if ($(this).val() == 'service1') {
            $('#information').empty()
            $('#information').append('<option value="stackplot">Population throughout years</option>');
            $('#information').append('<option value="lineplot">Life expectancy throughout years</option>');
            $('#information').append('<option value="pieplot">HDI</option>');
            $('#compare').empty()
        } else if ($(this).val() == 'service2') {
            $('#information').empty()
            $('#information').append('<option value="min">Minimum throughout years</option>');
            $('#information').append('<option value="max">Maximum throughout years</option>');
            $('#information').append('<option value="avg">Average throughout years</option>');
            $('#compare').append('  <div class="col-3">\n' +
                '                <label class="text-secondary">Fertility grater than:</label>\n' +
                '                <input type="text" class="form-control" name="fertility_no" value="-" placeholder="-">\n' +
                '            </div>\n' +
                '            <div class="col-3">\n' +
                '                <label class="text-secondary">Democracy grater than:</label>\n' +
                '                <input type="text" class="form-control" name="democracy_no"  value="-" placeholder="-">\n' +
                '            </div>\n' +
                '            <div class="col-3">\n' +
                '                <label class="text-secondary">Life expectancy grater than:</label>\n' +
                '                <input type="text" class="form-control" name="life_no" value="-" placeholder="-">\n' +
                '            </div>');
        }
    });