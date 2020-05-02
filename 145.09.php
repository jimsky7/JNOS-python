<?php

	/****
		This PHP script creates a page that contains a Google Chart showing packet radio
		log data over a time period.

		The Python script mailChart.py runs somewhere and creates the javascript data
		table that Google Chart is going to read. That javascript is saved in a file on
		the web server, and we use PHP's include() here to bring it into the table
		(a google.visualization.arrayToDataTable() structure).

		It makes a bar chart with time on the horizontal axis, and there's a 'filter'
		control that selects the 'low' and the 'high' dates that set boundaries on what's
		displayed (in real time, in that if you move the sliders on the control, the 
		chart will respond immediately).

		There's one glitch, which is that with certain sizes of date ranges the bars
		will overlap -- this seems to me to be an error -- so I've written a little code
		here to try to adjust, but it's imperfect.

		The analysis program (mailChart.py) not only reports the number of bytes each
		station sends during the logged time period, but it looks for callsigns in the
		'TO' of packets that it hasn't actually heard transmit. (This happens when
		stations are outside your range and too weak for the TNC to decode, consequently
		you never hear them transmit on your chosen channel.) These are added to the
		chart legend (only, not to the stats). This needs some attention at a future
		time...the number that appears for each of these stations is the number of
		-packets-, not bytes, that were addressed to those unheard stations. 

	****/

	$PHP_SELF = $_SERVER['PHP_SELF'];
	// echo "<!-- $PHP_SELF -->\n";
	$FREQUENCY = '145.09mHz';
	// Refresh periodically
	$REFRESH_SECONDS = '300';
	// Just refresh to self
	$REFRESH_URL     = $PHP_SELF;
	// Initial values
	$REFRESH_PARAMS  = '';
	$low = '';
	$high = '';
	// Pick up URI params
	if (isset($_GET['low'])) {
		$low = $_GET['low'];
		// echo "<!-- $low -->\n";
	}
	if (isset($_GET['high'])) {
		$high = $_GET['high'];
		// echo "<!-- $high -->\n";
	}
?>
<html>
	<head>
		<?php
			$content = $REFRESH_SECONDS;
			if(($low != '') && ($high != '')) {
				# Encode for URL
				$le  = str_replace('%27','',$low);
				$le  = trim($le, '\'');
				$le  = urlencode($le);
				# Encode for URL
				$he  = str_replace('%27','',$high);
				$he  = trim($he, '\'');
				$he  = urlencode($he);
				$content = "$REFRESH_SECONDS; url='$REFRESH_URL?low=%27$le%27&high=%27$he%27'";
			}
			echo "<meta http-equiv=\"refresh\" content=\"$content\" id=\"META_REFRESH\">";
		?>
		<!-- Google charts reference
			https://developers.google.com/chart/interactive/docs 
		-->
		<!-- Controls and Dashboards sample code is from
			https://developers.google.com/chart/interactive/docs/gallery/controls
		-->
		<!-- Control values and listener code is suggested here
			// https://developers.google.com/chart/interactive/docs/gallery/controls
		-->
		<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
		<script type="text/javascript">
	
		// Load the Visualization API and the controls package.
		google.charts.load('current', {'packages':['corechart', 'controls']});
	
		// Set a callback to run when the Google Visualization API is loaded.
		google.charts.setOnLoadCallback(drawDashboard);
	
		// Callback that creates and populates a data table,
		// instantiates a dashboard, a range slider and a pie chart,
		// passes in the data and draws it.
		function drawDashboard() {
	
			// Create our data table.
			var data = google.visualization.arrayToDataTable([
	    		<?php include '_data/mailChart-charts.txt'; ?>
			]);
	
			// Create a dashboard.
			var dashboard = new google.visualization.Dashboard(
	    		document.getElementById('dashboard_div'));
	
			// Create a range slider, passing some options
			var dateRangeSlider = new google.visualization.ControlWrapper({
				'controlType': 'DateRangeFilter',
	    		'containerId': 'filter_div',
	    	    'options': {
	    	    	'filterColumnLabel': 'Date'
				},
				<?php
					if ($low != '' and $high != '') {
				  		echo "'state': {'lowValue': new Date($low), 'highValue': new Date($high)}";
					}
					else {
				  		echo "'state': {'lowValue': new Date(Date.now() - 5 * 24 * 60 * 60 * 1000), 'highValue': new Date()}";
					}
				?>
			});

	    	// Create a chart, passing some options
	    	var packetChart = new google.visualization.ChartWrapper({
	    		'chartType': 'ColumnChart',
	    		'containerId': 'chart_div',
	    		'options': {
	    	    	width: '95%',
	    	    	height: '65%',
	    	    	legend: { position: 'top', maxLines: 5 },
	    	    	bar: { groupWidth: '70%' }, /* 70% */
	    	    	isStacked: true,
	    	    	/* vAxis: { scaleType: 'log'}, */ 
	    	    	'title':'Packet activity on <?php echo $FREQUENCY; ?> (in bytes per hour)'
	    		}
			});
	
			// Establish dependencies, declaring that 'filter' drives 'packetChart',
	    	// so that the pie chart will only display entries that are let through
	    	// given the chosen slider range.
	    	dashboard.bind(dateRangeSlider, packetChart);
	
	    	// Ask for an event callback when the date filter is changed
	    	google.visualization.events.addListener(dateRangeSlider, 'statechange', selectControl);
	
	    	// Draw the dashboard.
	    	dashboard.draw(data);
	    	
			// Adjust 'barWidth' : actually, don't adjust on first draw of the page,
			//   only adjust when user selects a different date range.
	    	// selectControl()
	
			function selectControl(e) {
				var cs = dateRangeSlider.getState()
				var low = cs.lowValue
				var high = cs.highValue
				// modify the <META> to reflect the new dates and refresh time
				var e = document.getElementById('META_REFRESH')
				var s = e.content
				var le = encodeURI(low).trim('\'')
				var he = encodeURI(high).trim('\'')
				s = "<?php echo $REFRESH_SECONDS; ?>; url='<?php echo $REFRESH_URL; ?>?low=%27"+le+"%27&high=%27"+he+"%27'"
				e.content = s
				/* Ad-hoc-ery: Adjust certain range otherwise the bar widths get wonky */
				var dLow = Date.parse(new Date(low))
				var dHigh = Date.parse(new Date(high))
				var days = 24 * 60 * 60 * 1000
				var barWidth = '70%'
				if ((dHigh-dLow) > (days * 7) && (dHigh-dLow) < (days * 11)) {
					barWidth = '30%'
				}
				if ((dHigh-dLow) > (days * 8) && (dHigh-dLow) < (days * 11)) {
					barWidth = '40%'
				}
				packetChart.setOption('bar.groupWidth', barWidth)
			}
		}
	
		</script>
	</head>

	<body>
		<!--Div that will hold the dashboard-->
		<div id="dashboard_div" style="height:95%;">
			<div style="font-family:sans-serif; color:darkgrey; height:14%; margin-bottom:10px;">
				<p style="margin-bottom:8px;">
				<b>Packet radio traffic on <?php echo $FREQUENCY; ?></b><br/>
				<span style="font-size:10pt; ">&nbsp;&nbsp;New data every hour. // 
					&nbsp;Use the sliders to select a date range. // Page reloads automatically every <?php echo intval($REFRESH_SECONDS/60); ?> minutes. // &nbsp;Resize the window and reload the page to change the chart size. 
					<br/>
					&nbsp;&nbsp;*Callsigns marked with an asterisk were not heard, although a BBS or other station 
					we <u>did</u> hear was communicating with them. "_CALLSIGN(BBS,packet count)"
				</span>
				<div id='DATE_TIME' style="height:25%; font-weight:bold; margin-bottom:4px;">
				</div>
				<script>var td=new Date(); var e =document.getElementById('DATE_TIME').innerHTML = td.toDateString()+" at "+td.toLocaleTimeString();</script>
		    	</p>
			</div>
			<!--Divs that will hold each control and chart-->
	      	<div id="filter_div" style="font-family:sans-serif; color:gray; height:8%;">
			</div>
	      	<div id="chart_div" style="height:80%;">
			</div>
		</div>
	</body>
</html>
