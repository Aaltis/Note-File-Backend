drop table if exists entries;
drop table if exists users;
create table users(
  userid integer primary key autoincrement,
  emailaddress text not null,
  password text not null
);

create table notes (
  id integer primary key autoincrement,
  ownerid integer not null,
  title text not null,
  text text not null,
  foreign key(ownerid) references user(userid)
);
create table files (
  id integer primary key autoincrement,
  ownerid integer not null,
  name text not null,
  type text not null,
  foreign key(ownerid) references user(userid)
);



