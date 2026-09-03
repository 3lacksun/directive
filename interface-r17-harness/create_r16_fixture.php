<?php
declare(strict_types=1);
if ($argc < 4) { fwrite(STDERR,"Usage: php create_r16_fixture.php <r16_dir> <db_path> <ordinary_user_count>\n"); exit(64); }
$r16Dir=rtrim($argv[1],'/'); $dbPath=$argv[2]; $userCount=(int)$argv[3];
if($userCount<0)throw new InvalidArgumentException('ordinary_user_count must be >=0');
if(!in_array('sqlite',PDO::getAvailableDrivers(),true)){fwrite(STDERR,"pdo_sqlite unavailable\n");exit(69);}
@mkdir(dirname($dbPath),0777,true); @unlink($dbPath); require $r16Dir.'/config.php';
$pdo=new PDO('sqlite:'.$dbPath,null,null,[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION,PDO::ATTR_DEFAULT_FETCH_MODE=>PDO::FETCH_ASSOC]); $pdo->exec('PRAGMA foreign_keys=ON'); migrate_schema($pdo);
$now='2026-09-01 20:00:00';
$insertUser=$pdo->prepare("INSERT INTO users(id,username,password_hash,pin_hash,role,permissions,disabled,email,display_name,force_password_change,session_version,created_at,last_login_at,account_state,auth_enrolled_at,auth_version) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)");
$insertUser->execute(['admin-r16','admin',password_hash('legacy-admin-password',PASSWORD_DEFAULT),password_hash('246810',PASSWORD_DEFAULT),'admin','{}',0,'admin@example.invalid','Owner',0,3,$now,$now,'active',$now,4]);
for($i=1;$i<=$userCount;$i++){$id='user-r16-'.$i;$insertUser->execute([$id,'legacy-user-'.$i,password_hash('legacy-user-'.$i,PASSWORD_DEFAULT),null,'user','{}',0,'','Legacy User '.$i,0,1,gmdate('Y-m-d H:i:s',strtotime($now)+$i),null,'active',$now,4]);}
$pdo->prepare("INSERT INTO conversations(id,user_id,title,model,system_prompt,prompt_id,prompt_version,temperature,max_tokens,json_mode,tags,archived,pinned,branch_of,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)")->execute(['conv-admin-r16','admin-r16','R16 preserved conversation','openai/gpt-oss-20b','','',0,0.7,2048,0,'[]',0,0,null,$now,$now]);
$pdo->prepare("INSERT INTO messages(id,conversation_id,role,content,attachments,meta,created_at) VALUES(?,?,?,?,?,?,?)")->execute(['msg-admin-r16','conv-admin-r16','user','R16 migration preservation marker','[]','{}',$now]);
$pdo->prepare("INSERT INTO memories(id,user_id,content,scope,enabled,memory_type,source_type,source_id,importance,expires_at,last_used_at,metadata,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)")->execute(['mem-admin-r16','admin-r16','Preserve this R16 memory exactly','global',1,'fact','manual','',4,null,null,'{}',$now,$now]);
if($userCount>0){$pdo->prepare("INSERT INTO conversations(id,user_id,title,model,system_prompt,prompt_id,prompt_version,temperature,max_tokens,json_mode,tags,archived,pinned,branch_of,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)")->execute(['conv-user-r16','user-r16-1','R16 user data','openai/gpt-oss-20b','','',0,0.7,2048,0,'[]',0,0,null,$now,$now]);$pdo->prepare("INSERT INTO messages(id,conversation_id,role,content,attachments,meta,created_at) VALUES(?,?,?,?,?,?,?)")->execute(['msg-user-r16','conv-user-r16','assistant','Preserved user message','[]','{}',$now]);}
$integrity=strtolower((string)$pdo->query('PRAGMA integrity_check')->fetchColumn()); if($integrity!=='ok')throw new RuntimeException('R16 fixture integrity_check failed: '.$integrity);
$out=['fixture'=>'r16','ordinary_user_count'=>$userCount,'users'=>(int)$pdo->query('SELECT COUNT(*) FROM users')->fetchColumn(),'conversations'=>(int)$pdo->query('SELECT COUNT(*) FROM conversations')->fetchColumn(),'messages'=>(int)$pdo->query('SELECT COUNT(*) FROM messages')->fetchColumn(),'memories'=>(int)$pdo->query('SELECT COUNT(*) FROM memories')->fetchColumn(),'sha256'=>hash_file('sha256',$dbPath),'integrity'=>$integrity];
file_put_contents($dbPath.'.fixture.json',json_encode($out,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES)); echo json_encode($out,JSON_UNESCAPED_SLASHES),"\n";
