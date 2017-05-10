<?php
$dbh = new PDO('sqlite:/home/intranet/intra/t3_trac/db/trac.db');
   /*
    * id
    * time
    * changetime
    * component
    * severity
    * priority
    * owner
    * reporter
    * cc
    * version
    * milestone
    * status
    * resolution
    * summary
    * description
    */
//match your actual scenario
$actual = "actual";
$sql = "SELECT distinct t.milestone
	FROM ticket t
	LEFT JOIN ticket_custom mt ON (t.id = mt.ticket AND mt.name = 'macro_task')
	WHERE mt.value != '' AND milestone > '2.9_2' /*AND status != 'closed' */
	order by milestone";
$milestones = array();    
foreach( $dbh->query($sql) as $row ){ 
    if(sizeof($milestones) >0)
        $previous_ms[$row['milestone']] = $milestones[sizeof($milestones)-1];
	    $milestones[] = $row['milestone'];
}
//print_r($previous_ms);
$mt=0;
$ms=0;
$last_mt=-1;
$last_ms=-1;
$sql = "SELECT distinct  mt.value as mt,t.milestone
	FROM ticket t
	LEFT JOIN ticket_custom mt ON (t.id = mt.ticket AND mt.name = 'macro_task')
	WHERE mt.value != ''  AND milestone > '2.9_2' /*AND status != 'closed' */
	order by mt, milestone ";
foreach ($dbh->query($sql) as $row) {
	if($last_mt != $row['mt']){
		$mt++;
	}
	if($last_ms != $row['milestone'] OR $last_mt != $row['mt'] ){
		$ms++;
	}
	$milestone_tasks[$row['milestone']][]="trac.mt$mt.ms". $ms;
	$last_mt = $row['mt'];
	$last_ms = $row['milestone'];
}
$sql = "SELECT t.id, t.owner, t.milestone, t.status,t.summary, t.description, t.priority
	, mt.value as mt
	, effort.value as effort
	, actual.value as actual_effort,
	(select time from ticket_change WHERE t.Id = ticket_change.ticket AND newvalue='closed' AND ticket_change.field='status' order by time desc limit 1) as closed_date,
    daysworked.value as daysworked
	FROM ticket t
	LEFT JOIN ticket_custom mt ON (t.id = mt.ticket AND mt.name = 'macro_task')
	LEFT JOIN ticket_custom effort ON (t.id = effort.ticket AND effort.name = 'estimatedhours')
	LEFT JOIN ticket_custom actual ON t.Id = actual.Ticket AND actual.name='estimatedfinal'
	LEFT JOIN ticket_custom daysworked ON t.Id = daysworked.Ticket AND daysworked.name='daysworked'
	WHERE mt != '' AND  milestone > '2.9_2' /*AND status != 'closed' */
	order by mt, milestone
";//group by t.id

$buffer="";
$depth = 0;
$mt=0;
$ms=0;
$last_mt=-1;
$last_ms=-1;
$last_task = array();
$daysworked= array();
to_buffer('task trac "trac" {');
$depth++;
to_buffer('start ${projectstart}');
foreach ($dbh->query($sql) as $row) {
	//close MacroTask
	if($last_mt != $row['mt'] AND $last_mt != -1){
		//close MileStone
        $depth--;
        to_buffer("}");
        //close MacroTask
		$depth--;
		to_buffer("}");
	}
	//create new MacroTask task
	if($last_mt != $row['mt']){
		$mt++;
		to_buffer('task mt'.$mt . ' "'. $row['mt'] .'" {');
		$depth++;
        $mts[] = $row['mt'];
        //$previous_MileStone = false;
	}
	//close MileStone task
	if($last_ms != $row['milestone'] AND $last_ms != -1 AND $last_mt == $row['mt'] ){
		$depth--;
		to_buffer("}");
	}
	//create new MileStone task
	if($last_ms != $row['milestone'] OR $last_mt != $row['mt'] ){
		$ms++;
		to_buffer('task ms'. $ms. '  "'. $row['milestone'] .'" {');
 		$depth++;
		//to_buffer("milestone");
		if($row['milestone'] == $milestones[0])
			to_buffer('start ${first_milestone}');
        else {
		    to_buffer("depends " . join(" ,",array_unique($milestone_tasks[$previous_ms[$row['milestone']]])));
        }
	}
	//create new task
	create_task($row,$mt,$ms);
	$last_mt = $row['mt'];
	$last_ms = $row['milestone'];
}
//close MileStone
$depth--;
to_buffer("}");
$depth--;
//close MacroTask
to_buffer("}");
//close trac
$depth--;
to_buffer('}');
foreach($mts as $mt => $desc){
    to_buffer('${task_report_by_mt "'.($mt+1).'" "'.$desc.'"}'); 
}
foreach($daysworked as $owner => $task_wd){
    to_buffer('supplement resource ' . $owner .'{');
    $depth++;
    foreach($task_wd as $task => $wd){
        to_buffer('actual:booking ' . $task . ' ' . $wd);
    }
    $depth--;
    to_buffer('}');
}

//file_put_contents("/home/max/trac.tji",$buffer);

function to_buffer($string){
	global $buffer,$depth;
	//$buffer .= "\n".str_pad('',$depth,"\t") . $string;
    echo "\n".str_pad('',$depth,"\t") . $string;
}

function create_task($row,$mt,$ms){
	global $depth,$actual,$daysworked;
	to_buffer('task t'. $row['id']. ' "'. $row['summary'] .'" {');
	$depth++;
	to_buffer("allocate ".$row['owner']);
	to_buffer("scheduling asap");
    to_buffer('priority ${'.$row['priority']."}");
    $has_plan_effort=false;
	if($row['effort']>0){
		to_buffer("effort ".$row['effort'] . "d");
        $has_plan_effort=1;
    }
	$has_effort=false;
	if($row['actual_effort']>0){
        if(!$has_plan_effort)
            to_buffer("effort ".$row['actual_effort'] . "d");
		to_buffer("$actual:effort ".$row['actual_effort'] . "d");
		$has_effort=true;
	}
    if(!$has_effort AND !$has_plan_effort)
        to_buffer("effort 0.1d" );
	if($row['status'] == 'closed') {
		//to_buffer("actual:scheduled");
		//to_buffer("actual:end ". date("Y-m-d",$row['closed_date']));
	}
	$depth--;
	to_buffer("}");
    if($row['daysworked']){
        if(!isset($daysworked[$row['owner']]))
            $daysworked[$row['owner']] = array();
        $daysworked[$row['owner']]["trac.mt$mt.ms$ms.t".$row['id']] = str_replace(array("\n","\r"),array(' {sloppy 2}, '),$row['daysworked']) . ' {sloppy 2}';
    }
} 
