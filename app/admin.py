from django.contrib import admin
from .models import *

# ==========================================
#  INLINES (Tablas hijas en edición)
# ==========================================

class DetalleFacturaInline(admin.TabularInline):
    model = DetalleFactura
    extra = 0
    autocomplete_fields = ['producto']

class DetalleReclamoInline(admin.TabularInline):
    model = DetalleReclamo
    extra = 0
    # La foto se carga aquí

class DetalleSolucionInline(admin.TabularInline):
    model = DetalleSolucion
    extra = 0
    autocomplete_fields = ['detalle_reclamo']

# ==========================================
#  ADMINISTRACIÓN GEOGRÁFICA (MAESTROS)
# ==========================================

@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Provincia)
class ProvinciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'pais')
    list_filter = ('pais',)
    autocomplete_fields = ['pais']
    search_fields = ('nombre',)

@admin.register(Ciudad)
class CiudadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'provincia', 'get_pais')
    list_filter = ('provincia__pais', 'provincia')
    search_fields = ('nombre',)
    autocomplete_fields = ['provincia']

    def get_pais(self, obj):
        return obj.provincia.pais.nombre
    get_pais.short_description = 'País'

# ==========================================
#  ADMINISTRACIÓN DEL NEGOCIO
# ==========================================

@admin.register(Restaurante)
class RestauranteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sucursal', 'ciudad', 'ruc')
    list_filter = ('ciudad__provincia__pais', 'ciudad')
    search_fields = ('nombre', 'ciudad__nombre')
    autocomplete_fields = ['ciudad']

@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'sueldo')

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('cedula', 'nombre', 'apellido', 'cargo', 'celular')
    list_filter = ('cargo',)
    search_fields = ('nombre', 'apellido', 'cedula')

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'telefono')
    search_fields = ('nombre', 'email')

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio')
    search_fields = ('nombre',)

@admin.register(TipoReclamo)
class TipoReclamoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')

@admin.register(TipoSolucion)
class TipoSolucionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')

# ==========================================
#  TRANSACCIONES Y PROCESOS
# ==========================================

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('codigo_factura', 'cliente', 'fecha', 'total')
    inlines = [DetalleFacturaInline]
    search_fields = ('codigo_factura',)
    autocomplete_fields = ['cliente', 'empleado']

@admin.register(Reclamo)
class ReclamoAdmin(admin.ModelAdmin):
    list_display = ('id', 'factura', 'estado', 'fecha')
    list_filter = ('estado', 'fecha')
    inlines = [DetalleReclamoInline]
    search_fields = ('factura__codigo_factura',)

@admin.register(DetalleReclamo)
class DetalleReclamoAdmin(admin.ModelAdmin):
    """
    Registrado para permitir búsqueda (autocomplete) desde Solución
    """
    list_display = ('id', 'reclamo', 'producto', 'tipo_reclamo')
    search_fields = ('producto__nombre', 'reclamo__id')

@admin.register(Solucion)
class SolucionAdmin(admin.ModelAdmin):
    list_display = ('id', 'reclamo', 'empleado', 'fecha_cierre')
    inlines = [DetalleSolucionInline]
    search_fields = ('reclamo__id',)