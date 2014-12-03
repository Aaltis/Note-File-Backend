drop table if exists entries;
drop table if exists users;
create table users(
  userid integer primary key autoincrement,
  emailaddress text not null,
  password text not null
);

create table entries (
  id integer primary key autoincrement,
  ownerid integer not null,
  title text not null,
  text text not null,
  foreign key(ownerid) references user(userid)
);


