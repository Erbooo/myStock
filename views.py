from django.shortcuts import render, redirect
from django.http import HttpResponse
import csv
from django.contrib import messages
from mystock.forms import StockCreateForm, StockSearchForm, StockUpdateForm, IssueForm, \
    ReceiveForm, ReorderLevelForm, StockHistorySearchForm
from mystock.models import Stock, StockHistory
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView


# Create your views here.\

def home(request):
    title = 'Welcome: This is the Home Page'
    context = {
        "title": title,
    }
    return render(request, "home.html", context)


@login_required
def list_item(request):
    header = 'Список'
    form = StockSearchForm(request.POST or None)
    queryset = Stock.objects.all()
    context = {
        "header": header,
        "queryset": queryset,
        "form": form,
    }
    if request.method == 'POST':
        queryset = Stock.objects.filter(item_name__icontains=form['item_name'].value(),
                                        category=form['category'].value(),
                                        )

    if form['export_to_CSV'].value():
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'arial; filename="Spisok.csv"'
        writer = csv.writer(response)
        writer.writerow(['CATEGORY', 'ITEM NAME', 'QUANTITY'])
        instance = queryset
        for stock in instance:
            writer.writerow([stock.category, stock.item_name, stock.quantity])
        return response

    context = {
        "form": form,
        "header": header,
        "queryset": queryset,
    }

    return render(request, "list_items.html", context)


@login_required
def add_items(request):
    form = StockCreateForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Успешно сохранено')
        return redirect('/list_items')
    context = {
        "form": form,
        "title": "Add Item",
    }
    return render(request, "add_items.html", context)


def update_items(request, pk):
    queryset = Stock.objects.get(id=pk)
    form = StockUpdateForm(instance=queryset)
    if request.method == 'POST':
        form = StockUpdateForm(request.POST, instance=queryset)
        if form.is_valid():
            form.save()
            messages.success(request, 'Успешно сохранено')
            return redirect('/list_items')
    context = {
        'form': form
    }
    return render(request, 'add_items.html', context)


def delete_items(request, pk):
    queryset = Stock.objects.get(id=pk)
    if request.method == 'POST':
        queryset.delete()
        messages.success(request, 'Удалено успешно')
        return redirect('/list_items')
    return render(request, 'delete_items.html')


def stock_detail(request, pk):
    queryset = Stock.objects.get(id=pk)
    context = {
        "queryset": queryset,
    }
    return render(request, "stock_detail.html", context)


def issue_items(request, pk):
    queryset = Stock.objects.get(id=pk)
    form = IssueForm(request.POST or None, instance=queryset)
    if form.is_valid():
        instance = form.save(commit=False)
        # instance.receive_quantity = 0
        instance.quantity -= instance.issue_quantity
        instance.issue_by = str(request.user)
        messages.success(request, "Выдано УСПЕШНО. = " + str(instance.quantity) + " " + str(
            instance.item_name) + " теперь осталось в складе")
        instance.save()
        issue_history = StockHistory(
            id=instance.id,
            last_updated=instance.last_updated,
            category_id=instance.category_id,
            item_name=instance.item_name,
            quantity=instance.quantity,
            issue_to=instance.issue_to,
            issue_by=instance.issue_by,
            issue_quantity=instance.issue_quantity,
        )
        issue_history.save()

        return redirect('/stock_detail/' + str(instance.id))
        # return HttpResponseRedirect(instance.get_absolute_url())

    context = {
        "title": 'Выпустить ' + str(queryset.item_name),
        "queryset": queryset,
        "form": form,
        "username": 'Выпустить By: ' + str(request.user),
    }
    return render(request, "add_items.html", context)


def receive_items(request, pk):
    queryset = Stock.objects.get(id=pk)
    form = ReceiveForm(request.POST or None, instance=queryset)
    if form.is_valid():
        instance = form.save(commit=False)
        # instance.issue_quantity = 0
        instance.quantity += instance.receive_quantity
        instance.save()
        receive_history = StockHistory(
            id=instance.id,
            last_updated=instance.last_updated,
            category_id=instance.category_id,
            item_name=instance.item_name,
            quantity=instance.quantity,
            receive_quantity=instance.receive_quantity,
            receive_by=instance.receive_by
        )
        receive_history.save()
        messages.success(request, "Получено УСПЕШНО. = " + str(instance.quantity) + " " + str(
            instance.item_name) + " сейчас в складе")

        return redirect('/stock_detail/' + str(instance.id))
        # return HttpResponseRedirect(instance.get_absolute_url())
    context = {
        "title": 'получить ' + str(queryset.item_name),
        "instance": queryset,
        "form": form,
        "username": 'получить By: ' + str(request.user),
    }
    return render(request, "add_items.html", context)


def reorder_level(request, pk):
    queryset = Stock.objects.get(id=pk)
    form = ReorderLevelForm(request.POST or None, instance=queryset)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.save()
        messages.success(request,
                         "Reorder level for " + str(instance.item_name) + " is updated to " + str(
                             instance.reorder_level))

        return redirect("/list_items")
    context = {
        "instance": queryset,
        "form": form,
    }
    return render(request, "add_items.html", context)


@login_required
def list_history(request):
    header = 'Список истории'
    queryset = StockHistory.objects.all()
    form = StockHistorySearchForm(request.POST or None)
    context = {
        "header": header,
        "queryset": queryset,
        "form": form,

    }

    if request.method == 'POST':
        category = form['category'].value()
        queryset = StockHistory.objects.filter(item_name__icontains=form['item_name'].value(),
                                               last_updated__range=[
                                                   form['start_date'].value(),
                                                   form['end_date'].value()
                                               ]
                                               )

        if (category != ''):
            queryset = queryset.filter(category_id=category)

        if form['export_to_CSV'].value() == True:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="Stock History.csv"'
            writer = csv.writer(response)
            writer.writerow(
                ['Категория',
                 'Наименование',
                 'Количество',
                 'Выдано',
                 'Плучаю',
                 'От кого',
                 'Кому',
                 'Дата'])
            instance = queryset
            for stock in instance:
                writer.writerow(
                    [stock.category,
                     stock.item_name,
                     stock.quantity,
                     stock.issue_quantity,
                     stock.receive_quantity,
                     stock.receive_by,
                     stock.issue_to,
                     stock.last_updated])
            return response

        context = {
            "form": form,
            "header": header,
            "queryset": queryset,
        }

    return render(request, "list_history.html", context)
