
drop table if exists users;
create table users(
  userid integer primary key autoincrement,
  emailaddress text not null,
  password text not null
);
drop table if exists notes;
create table notes (
  id integer primary key autoincrement,
  ownerid integer not null,
  title text not null,
  text text not null,
  foreign key(ownerid) references user(userid)
);
drop table if exists files;
create table files (
  id integer primary key autoincrement,
  ownerid integer not null,
  name text not null,
  foreign key(ownerid) references user(userid)
);



