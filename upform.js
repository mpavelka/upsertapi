function upform(formobj, options)
{	
	this.formobj 	= formobj;
	this.$formobj 	= $(formobj);
	this.options 	= options;
	
	this.defaults = {
		reloadOnSuccess 	: false,
		waitSpinner 		: $('<div>')
	}

	this.upformid 	= null; // set in init()
	this.url 		= null; // set in init()
	this.elements 	= null; // set in init()
	this.config 	= null; // set in init()

	this.init = function(upformid)
	{
		var that = this;
		this.config 	= $.extend({}, this.defaults, this.options);
		this.url 		= this.$formobj.data('upform-api');
		if (typeof(upformid) != 'undefined')
			this.upformid = upformid;
		else
			this.upformid = this.$formobj.data('upform-id');
		this.elements 	= this.$formobj.find('button,input,select,textarea');

		// Bind events (only once)
		if (typeof(this.events_bind) == 'undefined'){
			this.elements.each( function(i, elem)
			{
				var $elem = $(elem);
				if ($.inArray($elem.data('type'), ['scalar', 'scalar:bool', 'scalar:int']) != -1 )
				{
					$elem.on('change', function()
					{
						if ($(this).data('orig') != $(this).val()) $(this).addClass('changed');
						else $(this).removeClass('changed');
					});
				}
			});
			this.$formobj.on('submit', this.__submit);
			this.events_bind = true;
		}

		// load data if not new
		if (this.upformid == '!new') 
			this.__new();
		else 
			this.__load(this.upformid);

		// autofocus
		this.$formobj.find('[autofocus]').focus();
	}


	this.__buildUpsertorObj = function(elements)
	{
		var upsertor = {};

		// Insert inputs SCALAR values into upsertor object
		elements.each( function(i, elem)
		{
			var $elem = $(elem);
			if ($.inArray($elem.data('type'), ['scalar', 'scalar:bool', 'scalar:int']) != -1)
			{
				var val;
				// load value
				if ($elem.is('select'))
					val = $elem.find('option:selected').val();
				else
					val = $elem.val();
				if (val == undefined) val = '';
				// Skip inputs with unchanged values
				if ($elem.data('orig') == val) return true; // continue

				if (val == "")
					upsertor[$elem.attr('name')] = {'$unset' : 1};
				else {
					if ($elem.data('type') == 'scalar:int')
						val = parseInt(val);
					if ($elem.data('type') == 'scalar:bool')
						val = (val != 'false');
					upsertor[$elem.attr('name')] = {'$set' : val};
				}
			}
			else if ($elem.data('type') == 'fkey' && that.upformid == '!new')
			{
				upsertor[$elem.attr('name')] = {'$set' : $elem.val()};
			}
		});

		return upsertor;
	}

	this.__submit = function(e)
	{
		e.preventDefault();
		var that = this.upform;
		var upsertor = that.__buildUpsertorObj(that.elements);

		that.__enter_wait();

		$.ajax({
			type: "PUT",
			url: that.url + that.upformid,
			contentType: "application/json",
			data: JSON.stringify(upsertor)
		})
		.done( function(data, textStatus, jqXHR)
		{
			if (that.config.reloadOnSuccess) {
				location.reload();
				return;
			}
			that.$formobj.trigger('upform.submit.done', {data: data, textStatus: textStatus, jqXHR: jqXHR});
		})
		.fail(function(jqXHR, textStatus, errorThrown)
		{
			that.$formobj.trigger('upform.submit.fail', {jqXHR: jqXHR, textStatus: textStatus, errorThrown: errorThrown});
		})
		.always(function() {
			that.__leave_wait();
		});

		return false;
	}
	
	this.__populateElements = function(elements, data)
	{
		elements.each( function(i, elem)
		{
			var $elem = $(elem);
			
			if ($.inArray($elem.data('type'), ['scalar', 'scalar:bool', 'scalar:int']) != -1)
			{
				var val = String(data[elem.name]);
				if (val == 'undefined')
					val = '';

				$elem.val(val);
				$elem.data('orig', val);

				if ($elem.is('select') && val != '')
					$elem.find('option.temp').remove();

				$elem.trigger('change');
			}
		});
	}
	this.__load = function(upformid)
	{
		var that = this;
		that.upformid = upformid;

		that.__enter_wait();
		that.__reset();

		$.getJSON(that.url + that.upformid)
		.done(function(data, textStatus, jqXHR)
		{
			that.__populateElements(that.elements, data);
			that.$formobj.trigger('upform.load.done', {data: data, textStatus: textStatus, jqXHR: jqXHR});

		})
		.fail(function(jqXHR, textStatus, errorThrown)
		{
			that.$formobj.trigger('upform.load.fail', {jqXHR: jqXHR, textStatus: textStatus, errorThrown: errorThrown});
		})
		.always(function()
		{
			that.__leave_wait();
		});
	};

	this.__new = function(upformid)
	{
		var that = this;
		that.upformid = '!new';
		that.__reset();
	};

	this.__enter_wait = function()
	{
		this.config.waitSpinner.show();
		this.output = {}
		this.$formobj.find('button,input,select,textarea,.btn').attr("disabled", "disabled");
	};

	this.__leave_wait = function()
	{
		this.config.waitSpinner.hide();
		this.$formobj.find('button,input,select,textarea,.btn').removeAttr("disabled", "disabled");
	};

	this.__reset = function()
	{
		this.messages = []
		this.$formobj.trigger('upform.reset');

		var upformid = this.upformid;

		this.elements.each( function(i, elem)
		{
			var $elem = $(elem);
			if ($.inArray($elem.data('type'), ['scalar', 'scalar:bool', 'scalar:int']) != -1)
			{
				$elem.removeClass('changed');
				if($elem.data('default') != undefined)
					$elem.val($elem.data('default'))
				else
					if ( !$elem.is('select'))
						$elem.val('');

				$elem.data('orig', '');

				if ($elem.is('select') && $elem.find('option[value=""]').length == 0 && (upformid != '!new'))
					$elem.append('<option class="temp" value="" selected="selected"></option>');
			}
		});
	};

	return this;
};


// Install JQuery plugin

(function ( $ ) {

$.fn.upform = function(options)
{
	return this.each(function() {
		this.upform = new upform(this, options);
		this.upform.init();
	});
};

}( jQuery ));
