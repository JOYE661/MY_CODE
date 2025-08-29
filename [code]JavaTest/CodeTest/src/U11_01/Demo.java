package U11_01;
//统计一个英文文本中单词出现的次数
//（1）使用HashMap存储单词
//（2）相同的单词，个数+1

import java.io.*;
import java.util.HashSet;
import java.util.Scanner;
import java.util.Set;

public class Demo {

	public static void main(String[] args) throws ClassNotFoundException, IOException{
		// TODO Auto-generated method stub
		File file=new File("pro.txt");
		Scanner in=new Scanner(file);
		Set<Product> set=new HashSet<>();
		
		if(!file.exists()) {
			System.out.println("文件不存在");
			System.exit(0);
		}
		Product pro=new Product();
		while(in.hasNext()) {
			String line=in.nextLine();
			System.out.println(line);
			String[] items=line.split("\t");
			String re="\\D*";
			String pir=items[1].replaceAll(re,"").trim();
			//String pir=items[1].replace("kg","").replace("$","");
			pro=new Product(items[0],Double.parseDouble(pir),items[2],items[3]);
			set.add(pro);
			
			//for(String item:items) {
			//	System.out.println(item);
			//}
		}
		in.close();
		System.out.println("集合中的数据");
		for(Product p:set) {
			System.out.println(p);
		}
		//+++++++++++++++++++++++++++++++++++++++++++++

		ObjectOutputStream out=new ObjectOutputStream(new FileOutputStream("out.dat"));
		for(Product p:set) {
			out.writeObject(p);
		}
		out.close();
		
		//+++++++++++++++++++++++++++++++++++++++++++++
//			ObjectInputStream inn=new ObjectInputStream(new FileInputStream("out.dat"));
//			Object obj=inn.readObject();
//			while(obj!=null) {
//				System.out.println(obj);
//				obj=inn.readObject();
//			}
//			inn.close();
//		 
	}

}
